import time
import pyautogui
import logging
import tkinter as tk
import pytesseract
import re
from datetime import datetime
import calendar
from PIL import ImageEnhance, Image, ImageFilter
import threading
import os
import numpy as np
import cv2
import pyperclip

# Importe as tarefas e exponha-as como parte do módulo
from planresult_tasks import tasks

# Configure o caminho para o executável do Tesseract e o diretório tessdata
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ['TESSDATA_PREFIX'] = r"C:\Program Files\Tesseract-OCR\tessdata"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def limpar_texto(texto, filter_type="both"):
    """
    Remove caracteres do texto conforme o filtro desejado:
      - "numbers": remove tudo, exceto dígitos.
      - "letters": remove tudo, exceto letras (incluindo acentuadas).
      - "both": remove todos os caracteres que não sejam letras ou dígitos.
      - Caso outro valor seja informado, remove apenas caracteres especiais do início e fim.
    """
    texto = texto.strip()
    if filter_type == "numbers":
        texto = re.sub(r"[^\d]", "", texto)
    elif filter_type == "letters":
        texto = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ]", "", texto)
    elif filter_type == "both":
        # Permite letras e números
        texto = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ0-9]", "", texto)
    else:
        texto = re.sub(r'^[\W_]+|[\W_]+$', '', texto)
    return texto

def matches_filter(word, filter_type):
    """
    Verifica se a palavra corresponde ao filtro desejado:
      - Se filter_type == "numbers": apenas dígitos entre 1 e 31.
      - Se filter_type == "letters": apenas letras (incluindo acentuadas).
      - Se filter_type == "both": apenas letras e números.
      - Caso contrário, retorna True.
    """
    filter_type = filter_type.lower()
    if filter_type == "numbers":
        if not re.fullmatch(r"\d+", word):
            return False
        try:
            num = int(word)
            return 1 <= num <= 31
        except ValueError:
            return False
    elif filter_type == "letters":
        return re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", word) is not None
    elif filter_type == "both":
        return re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", word) is not None
    return True

def show_overlay(region, duration=1000):
    """
    Cria uma janela transparente de tela cheia que exibe um retângulo vermelho
    destacando a região onde o clique será realizado.
    
    Parâmetros:
      region: tupla (x, y, w, h) definindo a área a ser destacada.
      duration: tempo (em milissegundos) que o overlay ficará visível.
    """
    x, y, w, h = region
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.config(bg='black')
    root.attributes('-transparentcolor', 'black')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")

    canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg='black', highlightthickness=0)
    canvas.pack()
    canvas.create_rectangle(x, y, x + w, y + h, outline="red", width=4)

    root.after(duration, root.destroy)
    root.mainloop()

def preprocess_image_for_ocr(img):
    """
    Aplica técnicas de pré-processamento otimizadas com base nos resultados de execução.
    Foca em métodos que melhor detectaram números e remove métodos ineficazes.
    """
    # Lista para armazenar todas as versões processadas
    processed_images = []
    
    # Converte para array numpy para manipulação
    img_np = np.array(img)
    
    # MÉTODO 28 (62% confiança) - Prioridade máxima
    # -----------------------------------------------------------------------------------
    # Versão com melhor detecção de números em caixas coloridas
    # Processamento HSV com ajustes específicos
    img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
    
    # Aumenta a saturação para destacar cores
    img_hsv[:,:,1] = np.clip(img_hsv[:,:,1] * 1.4, 0, 255).astype(np.uint8)
    img_enhanced = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB)
    processed_images.append(Image.fromarray(img_enhanced))
    
    # Versão com threshold específico - variação do método 28
    img_gray = cv2.cvtColor(img_enhanced, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY)
    processed_images.append(Image.fromarray(thresh))
    
    # MÉTODO 2 (59% confiança) - Segunda prioridade
    # -----------------------------------------------------------------------------------
    # Inversão para texto claro em fundo escuro
    _, dark_bg_thresh = cv2.threshold(np.array(img.convert("L")), 160, 255, cv2.THRESH_BINARY_INV)
    processed_images.append(Image.fromarray(dark_bg_thresh))
    
    # Variação do método 2 com diferentes thresholds
    dark_thresholds = [140, 160, 180]
    for thresh_val in dark_thresholds:
        _, dark_var = cv2.threshold(np.array(img.convert("L")), thresh_val, 255, cv2.THRESH_BINARY_INV)
        processed_images.append(Image.fromarray(dark_var))
    
    # MÉTODO 22 (57% confiança) - Terceira prioridade
    # -----------------------------------------------------------------------------------
    # Processamento de canais de cor e detecção específica
    r_channel = img_np[:,:,0]
    g_channel = img_np[:,:,1]
    b_channel = img_np[:,:,2]
    
    # Variações de manipulação de canais
    # Detecção de canais com base em diferenças entre R, G, B
    channel_diff = np.absolute(r_channel.astype(np.int16) - b_channel.astype(np.int16))
    channel_diff = np.clip(channel_diff * 2, 0, 255).astype(np.uint8)
    _, channel_thresh = cv2.threshold(channel_diff, 30, 255, cv2.THRESH_BINARY)
    processed_images.append(Image.fromarray(channel_thresh))
    
    # MÉTODO 13 (41% confiança) e MÉTODO 27 (41% confiança)
    # -----------------------------------------------------------------------------------
    # Versões com alta nitidez e contraste
    gray = img.convert("L")
    
    # Contraste alto + nitidez (otimizado)
    contrast_sharp = ImageEnhance.Contrast(gray).enhance(2.5).filter(ImageFilter.SHARPEN)
    processed_images.append(contrast_sharp)
    
    # Nitidez adicional para melhorar bordas
    extra_sharp = contrast_sharp.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
    processed_images.append(extra_sharp)
    
    # TÉCNICAS PARA TEXTO CLARO EM FUNDO ESCURO (cinza, preto)
    # -----------------------------------------------------------------------------------
    # Inversão simples (útil para texto branco em fundo escuro)
    inverted = Image.fromarray(255 - img_np)
    processed_images.append(inverted)
    
    # Thresholding adaptativo para texto em fundo escuro
    cv_gray = np.array(gray)
    
    # Adaptativo com diferentes janelas - melhor para números pequenos em fundos variados
    adaptive_thresh1 = cv2.adaptiveThreshold(
        cv_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 2
    )
    processed_images.append(Image.fromarray(adaptive_thresh1))
    
    adaptive_thresh2 = cv2.adaptiveThreshold(
        cv_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 3
    )
    processed_images.append(Image.fromarray(adaptive_thresh2))
    
    # MANIPULAÇÃO DE COR PARA FUNDOS COLORIDOS (rosa, cinza)
    # -----------------------------------------------------------------------------------
    # Rosa/roxo claro em HSV com faixas mais precisas
    lower_pink = np.array([140, 50, 150])
    upper_pink = np.array([170, 255, 255])
    pink_mask_hsv = cv2.inRange(img_hsv, lower_pink, upper_pink)
    pink_mask_inv = cv2.bitwise_not(pink_mask_hsv)
    processed_images.append(Image.fromarray(pink_mask_inv))
    
    # Cinza claro em HSV
    lower_gray = np.array([0, 0, 180])
    upper_gray = np.array([180, 30, 255])
    gray_mask_hsv = cv2.inRange(img_hsv, lower_gray, upper_gray)
    gray_mask_inv = cv2.bitwise_not(gray_mask_hsv)
    processed_images.append(Image.fromarray(gray_mask_inv))
    
    # Cinza escuro/preto
    lower_dark_gray = np.array([0, 0, 0])
    upper_dark_gray = np.array([180, 30, 80])
    dark_gray_mask = cv2.inRange(img_hsv, lower_dark_gray, upper_dark_gray)
    dark_gray_mask_inv = cv2.bitwise_not(dark_gray_mask)
    processed_images.append(Image.fromarray(dark_gray_mask_inv))
    
    # EQUALIZAÇÃO E APRIMORAMENTO DE LUMINOSIDADE
    # -----------------------------------------------------------------------------------
    # Lab color space processing - bom para números em fundos coloridos diversos
    lab_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_img)
    
    # Equaliza o canal L (luminosidade) - técnica que foi bem sucedida
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l_channel)
    
    # Recombina os canais
    updated_lab_img = cv2.merge((cl, a_channel, b_channel))
    
    # Converte de volta para RGB e depois para escala de cinza
    enhanced_img = cv2.cvtColor(updated_lab_img, cv2.COLOR_LAB2RGB)
    enhanced_gray = cv2.cvtColor(enhanced_img, cv2.COLOR_RGB2GRAY)
    
    # Aplica thresholding na imagem melhorada
    _, binary_enhanced = cv2.threshold(enhanced_gray, 127, 255, cv2.THRESH_BINARY)
    processed_images.append(Image.fromarray(binary_enhanced))
    
    # Versão invertida para texto claro em fundo escuro
    _, binary_enhanced_inv = cv2.threshold(enhanced_gray, 127, 255, cv2.THRESH_BINARY_INV)
    processed_images.append(Image.fromarray(binary_enhanced_inv))
    
    # COMBINAÇÕES OTIMIZADAS - mescla técnicas bem sucedidas
    # -----------------------------------------------------------------------------------
    
    # Combinação: alta nitidez + contraste elevado
    contrast_highest = ImageEnhance.Contrast(gray).enhance(3.0)
    sharpened_strong = contrast_highest.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
    processed_images.append(sharpened_strong)
    
    # Mescla lab e hsv para capturar o melhor dos dois mundos
    merged_img = cv2.addWeighted(enhanced_gray, 0.5, img_gray, 0.5, 0)
    _, merged_thresh = cv2.threshold(merged_img, 140, 255, cv2.THRESH_BINARY)
    processed_images.append(Image.fromarray(merged_thresh))
    
    # Filtra imagens válidas
    valid_images = []
    for img in processed_images:
        try:
            if img.mode in ['RGB', 'L', '1']:
                valid_images.append(img)
        except Exception as e:
            logging.debug(f"Erro ao processar uma das imagens: {e}")
    
    print(f"Gerando {len(valid_images)} variações otimizadas de pré-processamento para OCR")
    
    return valid_images

def locate_image_with_retry(image_path, region=None, confidence=0.9, max_attempts=3, scales=None):
    """
    Tenta localizar uma imagem com diferentes escalas e níveis de confiança.
    """
    if scales is None:
        scales = [1.0, 0.95, 1.05]  # Tenta com escala original e ±5%
    
    for attempt in range(max_attempts):
        # Tenta localizar com diferentes escalas
        for scale in scales:
            try:
                if scale != 1.0:
                    # Carrega e redimensiona a imagem de referência
                    ref_img = Image.open(image_path)
                    new_width = int(ref_img.width * scale)
                    new_height = int(ref_img.height * scale)
                    scaled_img = ref_img.resize((new_width, new_height))
                    
                    # Salva temporariamente para usar com pyautogui
                    temp_path = f"temp_scaled_{scale}.png"
                    scaled_img.save(temp_path)
                    
                    if region:
                        location = pyautogui.locateOnScreen(temp_path, region=region, confidence=confidence)
                    else:
                        location = pyautogui.locateOnScreen(temp_path, confidence=confidence)
                    
                    os.remove(temp_path)  # Limpa arquivo temporário
                else:
                    if region:
                        location = pyautogui.locateOnScreen(image_path, region=region, confidence=confidence)
                    else:
                        location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                
                if location:
                    return location
            except Exception as e:
                logging.debug(f"Erro ao buscar imagem com escala {scale}: {e}")
                continue
        
        # Se a escala não funcionou, tente reduzir a confiança
        adjusted_confidence = max(0.7, confidence - 0.05 * (attempt + 1))
        logging.debug(f"Ajustando confiança para {adjusted_confidence}")
        
        try:
            if region:
                location = pyautogui.locateOnScreen(image_path, region=region, confidence=adjusted_confidence)
            else:
                location = pyautogui.locateOnScreen(image_path, confidence=adjusted_confidence)
            
            if location:
                return location
        except Exception as e:
            logging.debug(f"Erro ao buscar imagem com confiança ajustada: {e}")
        
        # Pequena pausa entre tentativas
        time.sleep(0.5)
    
    return None

def find_text_with_multiple_preprocessing(region_img, target_text, filter_type, early_confidence_threshold=75.0):
    """
    Tenta encontrar o texto usando múltiplas versões pré-processadas da imagem.
    Retorna as caixas encontradas junto com seus scores de confiança.
    Se encontrar um resultado com confiança acima do threshold, retorna imediatamente.
    """
    processed_images = preprocess_image_for_ocr(region_img)
    
    # Configurações OCR com prioridade para PSM 7 e 8 (melhores para números isolados)
    configs = [
        r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789',  # Linha única - limitada a números
        r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789',  # Palavra única - limitada a números
        r'--oem 3 --psm 6',  # Layout de página mais comum
        r'--oem 3 --psm 11'  # Texto esparso
    ]
    
    all_found_boxes = []
    all_confidence_scores = []
    
    print(f"Buscando texto '{target_text}' com limiar de confiança de {early_confidence_threshold}%")
    
    # Bônus para métodos prioritários
    high_confidence_bonus = 8.0  # Bônus mais alto para os primeiros métodos (optimizados)
    
    for img_index, img in enumerate(processed_images):
        for config_index, config in enumerate(configs):
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=config)
                
                recognized_words = [limpar_texto(w, filter_type) for w in data['text'] if w.strip()]
                recognized_words = [w for w in recognized_words if matches_filter(w, filter_type)]
                
                # Print numbers found in OCR
                if filter_type == "numbers":
                    if recognized_words:
                        print(f"OCR Numbers found (método {img_index+1}/{len(processed_images)}): {recognized_words}")
                elif filter_type == "both":
                    # Filter only numeric words to print
                    numeric_words = [w for w in recognized_words if w.isdigit()]
                    if numeric_words:
                        print(f"OCR Numbers found (método {img_index+1}/{len(processed_images)}): {numeric_words}")
                
                target_words = [limpar_texto(word, filter_type) for word in target_text.split()]
                target_words = [w for w in target_words if matches_filter(w, filter_type)]
                n_words = len(target_words)
                
                for idx in range(len(data['text']) - n_words + 1):
                    candidate = [limpar_texto(data['text'][j], filter_type) for j in range(idx, idx + n_words)]
                    if not all(candidate):
                        continue
                    if not all(matches_filter(word, filter_type) for word in candidate):
                        continue
                    
                    # Verifica se as palavras candidatas correspondem às palavras alvo
                    if all(candidate[k].lower() == target_words[k].lower() for k in range(n_words)):
                        # Calcula o score de confiança médio para essas palavras
                        confidence_values = [float(data['conf'][j]) for j in range(idx, idx + n_words) if float(data['conf'][j]) > 0]
                        
                        if confidence_values:
                            avg_confidence = sum(confidence_values) / len(confidence_values)
                        else:
                            avg_confidence = 0
                            
                        lefts = [data['left'][j] for j in range(idx, idx + n_words)]
                        tops = [data['top'][j] for j in range(idx, idx + n_words)]
                        rights = [data['left'][j] + data['width'][j] for j in range(idx, idx + n_words)]
                        bottoms = [data['top'][j] + data['height'][j] for j in range(idx, idx + n_words)]
                        
                        min_left = min(lefts)
                        min_top = min(tops)
                        max_right = max(rights)
                        max_bottom = max(bottoms)
                        
                        box = (min_left, min_top, max_right - min_left, max_bottom - min_top)
                        
                        # Adicionar bônus conforme o processamento e configuração
                        config_bonus = 0
                        if filter_type == "numbers" and config_index < 2:  # PSM 7 e 8 com whitelist
                            config_bonus = 8 if config_index == 0 else 5
                        
                        # Adiciona bônus para os métodos de alta prioridade
                        method_bonus = 0
                        if img_index < 10:  # Os primeiros métodos são específicos para melhor desempenho
                            method_bonus = high_confidence_bonus * (1.0 - (img_index / 10.0))
                        
                        final_confidence = avg_confidence + config_bonus + method_bonus
                        
                        print(f"Encontrado '{' '.join(candidate)}' com confiança: {final_confidence:.2f}% (método {img_index+1})")
                        
                        # Se a confiança for alta o suficiente, retorna imediatamente
                        if final_confidence >= early_confidence_threshold:
                            print(f">>> Detecção com alta confiança ({final_confidence:.2f}%) encontrada! Executando ação imediatamente.")
                            return [box], [final_confidence], True
                        
                        # Adicione o box e sua pontuação de confiança para comparação posterior
                        all_found_boxes.append(box)
                        all_confidence_scores.append(final_confidence)
            except Exception as e:
                logging.debug(f"Erro em OCR com configuração {config}: {e}")
                continue
    
    return all_found_boxes, all_confidence_scores, False

def click_images(tasks, default_confidence=0.9, default_margin=50):
    """
    Itera sobre as tasks e executa as ações necessárias com detecção aprimorada.
    """
    i = 0
    max_attempts = 4  # Sempre 3 tentativas para cada tarefa
    task_failures = {}  # Rastreia quantas vezes uma tarefa falhou após backtracking
    
    while i < len(tasks):
        task = tasks[i]
        region = task.get('region')
        delay = task.get('delay', 0)
        location = None
        attempts = 0
        
        # Define o limiar de confiança para ação imediata
        early_confidence_threshold = task.get('early_confidence', 75.0)
        
        # Nome da tarefa para logs (texto ou nome do arquivo de imagem)
        task_name = task.get('text', task.get('image', f"Tarefa {i+1}"))
        
        logging.info(f"Iniciando tarefa {i+1}/{len(tasks)}: {task_name}")
        
        while attempts < max_attempts and location is None:
            try:
                if 'text' in task:
                    target_text = task.get('text')
                    filter_type = task.get('char_type', 'both').lower()
                    
                    # Verifica se a região está definida
                    if not region:
                        logging.warning("Nenhuma região definida para OCR. É necessário especificar uma região válida.")
                        break
                    
                    logging.info(f"Buscando o texto '{target_text}' em TODA a região {region} com filtro '{filter_type}' (tentativa {attempts+1} de {max_attempts})")
                    
                    # Captura a screenshot da área completa definida pela região
                    # Formato da região: (x, y, largura, altura)
                    region_img = pyautogui.screenshot(region=region)
                    
                    # Verifica se a imagem foi capturada corretamente
                    if not region_img or region_img.width <= 1 or region_img.height <= 1:
                        logging.warning(f"Falha ao capturar a região {region} para OCR. Verifique se as coordenadas são válidas.")
                        attempts += 1
                        continue
                    
                    logging.info(f"Área capturada para OCR: {region[2]}x{region[3]} pixels")
                    
                    # Usa a função melhorada de detecção de texto processando TODA a área da imagem
                    found_boxes, confidence_scores, early_match = find_text_with_multiple_preprocessing(
                        region_img, target_text, filter_type, early_confidence_threshold
                    )
                    
                    if found_boxes:
                        # Verifica se todas as confianças estão abaixo do limiar
                        if all(score < early_confidence_threshold for score in confidence_scores):
                            logging.info(f"Todas as confianças para '{target_text}' estão abaixo de {early_confidence_threshold}%. " +
                                         "Presumindo que o alvo já foi clicado. Avançando para a próxima tarefa.")
                            location = "skip"  # Sinalização para pular o clique
                            break
                            
                        if early_match:
                            # Se houver uma correspondência antecipada, use-a diretamente
                            selected_box_relative = found_boxes[0]
                            logging.info(f"Usando detecção antecipada com confiança: {confidence_scores[0]:.2f}%")
                        elif task.get('best_confidence', True):
                            # Senão, selecione o box com maior confiança
                            best_index = confidence_scores.index(max(confidence_scores))
                            selected_box_relative = found_boxes[best_index]
                            logging.info(f"Selecionada a detecção com maior confiança: {max(confidence_scores):.2f}%")
                        else:
                            # Mantém o comportamento anterior para compatibilidade
                            occurrence = task.get('occurrence', 1)
                            if len(found_boxes) >= occurrence:
                                selected_box_relative = found_boxes[occurrence - 1]
                            else:
                                selected_box_relative = found_boxes[-1]
                        
                        # Converter coordenadas relativas para absolutas
                        # Isso garante que o clique ocorra na posição correta dentro da região especificada
                        selected_box = (
                            region[0] + selected_box_relative[0],
                            region[1] + selected_box_relative[1],
                            selected_box_relative[2],
                            selected_box_relative[3]
                        )
                        
                        logging.info(f"Texto '{target_text}' encontrado na posição {selected_box_relative} dentro da região {region}")
                        location = selected_box
                    else:
                        logging.warning(f"Texto '{target_text}' não encontrado em toda a região {region}. Tentativa {attempts+1} de {max_attempts}.")
                
                elif 'image' in task:
                    image = task.get('image')
                    confidence = task.get('confidence', default_confidence)
                    specific = task.get('specific', True)
                    
                    if specific:
                        # Se for específico, busca apenas na região definida
                        logging.info(f"Buscando {image} na região {region} com confiança {confidence} (tentativa {attempts+1} de {max_attempts})")
                        location = locate_image_with_retry(image, region=region, confidence=confidence)
                    else:
                        # Se não for específico, busca na tela inteira
                        logging.info(f"Buscando {image} em toda a tela com confiança {confidence} (tentativa {attempts+1} de {max_attempts})")
                        location = locate_image_with_retry(image, confidence=confidence)
                else:
                    logging.warning("Task sem chave 'text' ou 'image' definida.")
                    break
            except Exception as e:
                logging.error(f"Erro na tarefa {i+1}, tentativa {attempts+1}: {e}")
            
            # Se não encontrou, aguarde um pouco antes da próxima tentativa
            if not location:
                time.sleep(max(0.5, attempts * 0.5))  # Aumenta o tempo de espera gradualmente
                
            attempts += 1
        
        if location:
            # Tarefa bem-sucedida, avança para a próxima
            logging.info(f"✓ Tarefa {i+1}/{len(tasks)}: '{task_name}' concluída com sucesso.")
            i += 1
            
            # Se foi marcado para pular, avança para a próxima tarefa sem clicar
            if location == "skip":
                logging.info("Pulando ação de clique para esta tarefa.")
                continue
                
            # Inicia o overlay em uma thread separada
            overlay_thread = threading.Thread(target=show_overlay, args=(location, 1000))
            overlay_thread.start()
            
            # Pequeno delay para garantir que o overlay seja exibido antes do clique
            time.sleep(0.2)
            
            # Calcula o ponto de clique (centro do elemento)
            click_point = pyautogui.center(location)
            
            # Movimento suave do mouse para reduzir erros de clique
            pyautogui.moveTo(click_point.x, click_point.y, duration=0.1)

            # Pequena pausa para garantir que o movimento foi registrado antes do clique
            time.sleep(1)

            # Verifica qual botão do mouse usar para o clique
            mouse_button = task.get('mouse_button', 'left').lower()
            if mouse_button == 'right':
                pyautogui.rightClick()
                logging.info(f"Clique com botão direito realizado na posição {click_point}. Aguardando {delay} segundos.")
            elif mouse_button == 'double' or mouse_button == 'double left':
                pyautogui.doubleClick()
                logging.info(f"Clique duplo com botão esquerdo realizado na posição {click_point}. Aguardando {delay} segundos.")
            else:
                pyautogui.click()
                logging.info(f"Clique com botão esquerdo realizado na posição {click_point}. Aguardando {delay} segundos.")
            
            # Verifica se a tarefa tem o campo 'sendtext' e digita o texto após o clique
            if 'sendtext' in task and task['sendtext']:
                full_text_command = task['sendtext']
                logging.info(f"Processando sendtext: '{full_text_command}'")

                # Processa comandos especiais no início da string
                text_to_write = full_text_command
                commands_processed = True
                while commands_processed:
                    commands_processed = False
                    # Padroniza para minúsculas para facilitar a correspondência
                    lower_text = text_to_write.lower() 
                    
                    if lower_text.startswith('{ctrl}a'):
                        logging.info("Executando comando: CTRL+A (Selecionar Tudo)")
                        pyautogui.hotkey('ctrl', 'a')
                        # Remove o comando original, preservando o caso do restante
                        text_to_write = text_to_write[len('{ctrl}a'):]
                        commands_processed = True
                        time.sleep(0.1) # Pequena pausa
                    elif lower_text.startswith('{del}'):
                        logging.info("Executando comando: DEL (Deletar)")
                        pyautogui.press('delete')
                        text_to_write = text_to_write[len('{del}'):]
                        commands_processed = True
                        time.sleep(0.1) # Pequena pausa
                    elif lower_text.startswith('{tab}'):
                        logging.info("Executando comando: TAB")
                        pyautogui.press('tab')
                        text_to_write = text_to_write[len('{tab}'):]
                        commands_processed = True
                        time.sleep(0.1)
                    elif lower_text.startswith('{enter}'):
                        logging.info("Executando comando: ENTER")
                        pyautogui.press('enter')
                        text_to_write = text_to_write[len('{enter}'):]
                        commands_processed = True
                        time.sleep(0.1)
                    # Adicionar mais comandos aqui se necessário (ex: {F1}, {ESC})


                # Digita o texto restante
                if text_to_write:
                    logging.info(f"Colando texto restante: '{text_to_write}'")
                    # Copia para o clipboard
                    pyperclip.copy(text_to_write) 
                    # Simula Ctrl+V para colar
                    pyautogui.hotkey('ctrl', 'v') 
                
                time.sleep(0.5)  # Pequena pausa após processar sendtext
            
            # Aguarda o overlay finalizar, se necessário
            overlay_thread.join()
            time.sleep(delay)
        else:
            # Tarefa falhou após todas as tentativas
            backtrack = task.get('backtrack', False)
            
            # Se a tarefa tiver backtrack=True e não for a primeira tarefa
            if backtrack and i > 0:
                # Verifica se já tentamos muitas vezes este backtrack para evitar loops infinitos
                task_failures.setdefault(i, 0)
                task_failures[i] += 1
                
                if task_failures[i] <= 2:  # Limita a 2 tentativas de backtracking por tarefa
                    # Volta para o passo anterior independentemente do valor de backtrack desse passo
                    prev_task_name = tasks[i-1].get('text', tasks[i-1].get('image', f"Tarefa {i}"))
                    logging.info(f"✗ Tarefa {i+1}/{len(tasks)}: '{task_name}' falhou. BACKTRACKING para tarefa {i}/{len(tasks)}: '{prev_task_name}'")
                    i -= 1  # Volta para a tarefa anterior
                else:
                    # Se já tentamos backtracking muitas vezes, avança
                    logging.info(f"✗ Tarefa {i+1}/{len(tasks)}: '{task_name}' falhou após múltiplas tentativas de backtracking. Avançando para a próxima tarefa.")
                    i += 1
            else:
                # Se não tem backtrack ou é a primeira tarefa, avança
                if backtrack:
                    logging.info(f"✗ Tarefa {i+1}/{len(tasks)}: '{task_name}' falhou mas é a primeira tarefa (não é possível fazer backtracking). Avançando.")
                else:
                    logging.info(f"✗ Tarefa {i+1}/{len(tasks)}: '{task_name}' falhou e tem 'backtrack': False. Avançando para a próxima tarefa.")
                i += 1

# Execute apenas se o script for executado diretamente (não na importação)
if __name__ == '__main__':
    # Import tasks from a.py (assuming a.py is in the same directory or Python path)
    # Check if tasks is a list and not empty
    if isinstance(tasks, list) and tasks:
        # Check if the first element is also a list (indicating a list of lists)
        if isinstance(tasks[0], list):
            logging.info(f"Detected multiple task lists ({len(tasks)} lists). Executing sequentially.")
            # Iterate through each list of tasks
            for i, task_list in enumerate(tasks):
                if isinstance(task_list, list):
                    logging.info(f"--- Starting task list {i+1}/{len(tasks)} ({len(task_list)} tasks) ---")
                    click_images(task_list) # Pass the individual list to the function
                    logging.info(f"--- Finished task list {i+1}/{len(tasks)} ---")
                else:
                    logging.warning(f"Item {i} in the main list is not a list of tasks. Skipping.")
        else:
            # Assume it's a single flat list of tasks
            logging.info("Detected a single task list. Executing.")
            click_images(tasks)
    elif isinstance(tasks, list) and not tasks:
        logging.info("The imported 'tasks' list is empty. Nothing to execute.")
    else:
        logging.error(f"The imported 'tasks' is not a list. Type: {type(tasks)}. Cannot execute.")
