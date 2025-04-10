# RPA Automation Suite

## 📌 Introdução
A **RPA Automation Suite** é uma ferramenta completa para criação de automação de processos robotizados (**RPA**). Com ela, é possível interagir com:

- **Páginas Web**: Automatize tarefas repetitivas em sites.
- **Elementos Visuais na Tela**: Capture e interaja com elementos gráficos usando OCR.
- **Aplicativos Windows**: Controle programas e janelas do sistema.

## 📋 Requisitos
Antes de iniciar, certifique-se de ter os seguintes requisitos instalados:

### 🖥️ Software Necessário
- **Python** 3.6+
- **Drivers de Navegadores**:
  - Edge: `msedgedriver.exe`
  - Chrome: `chromedriver.exe`
  - Firefox: `geckodriver.exe`
  - Internet Explorer (Opcional): `IEDriverServer.exe`
- **Bibliotecas Python**:
  - `BotCity`
  - `Selenium`
  - `PIL`
  - `pyautogui`
  - `keyboard`
  - `tkinter`
- **OCR**:
  - **Tesseract OCR** para reconhecimento de texto em imagens

## 🚀 Instalação
1. Instale o Python e as bibliotecas necessárias:
   ```sh
   pip install -r requirements.txt
   ```
2. Instale o **Tesseract OCR** e configure o caminho corretamente.
3. Baixe os drivers dos navegadores compatíveis e configure no sistema.

## 🌐 Web Automation
### Funcionalidades
✅ Captura elementos HTML em páginas web  
✅ Suporte para frames e iframes  
✅ Identifica propriedades (ID, classe, XPath, etc.)  
✅ Monitora mudanças de URL automaticamente  

### Tipos de Interação
- **Click**: Clique em botões e links.
- **Input**: Inserção de texto em formulários.
- **Copy**: Extração de texto de elementos.
- **OCR**: Extração de texto de imagens.

### Como Usar
1. Inicie a ferramenta e selecione **"Web Automation"**.
2. Digite a URL e escolha o navegador.
3. Clique em **"Start Capture"**.
4. Posicione o mouse sobre o elemento e pressione `HOME`.
5. Configure o nome e a interação desejada.
6. Gere o código com **"Generate BotCity Code"**.

## 👁️ Vision Automation
### Funcionalidades
✅ Captura regiões da tela independente da aplicação  
✅ Reconhece texto e imagens na tela  
✅ Suporta múltiplos monitores  

### Como Usar
1. Selecione a aba **"Vision Automation"**.
2. Clique em **"Select Screen Area"**.
3. Selecione a região da tela a ser capturada.
4. Configure o nome, tipo e opções.
5. Gere o código com **"Generate Vision Code"**.

### Como Usar
1. Execute o **Windows Element Inspector**.
2. Passe o mouse sobre o elemento desejado.
3. Pressione `HOME` para capturar.
4. Selecione o tipo de ação (click, input, etc.).
5. Copie o código gerado.
6. Pressione `ESC` para sair.

## ⚙️ Configurações
- **Drivers de Navegadores**: Configure os caminhos corretamente.
- **OCR**: Defina a pasta do **Tesseract OCR**.
- **Imagens**: Configure a pasta para salvar screenshots.

## 📝 Exemplo de Código

![image](https://github.com/user-attachments/assets/72278dd4-1791-419a-8479-cb6cb8cf1955)

![image](https://github.com/user-attachments/assets/2176cc13-6225-47c9-aa95-b1cb72d8e917)


```python
from botcity.web import By, WebBot
import time
import os
import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class PracticetestautomationFunctions:
    def __init__(self, webbot):
        self.webbot = webbot
        self.max_attempts = 3
        # Variáveis para armazenar textos extraídos
        self.vars = {}
        # Armazenar os handles das janelas/abas
        self.window_handles = {}
        # Pasta para salvar screenshots temporários
        self.screenshots_folder = "C:/Users/matheus/Documents/test"

    def start_navigation(self):
        """Inicia a navegação e configura as janelas iniciais."""
        self.webbot.browse("https://practicetestautomation.com/practice-test-login/")
        # Armazenar o handle da janela principal
        main_handle = self.webbot.driver.current_window_handle
        self.window_handles['main'] = main_handle
        # Aguardar carregamento da página
        self.webbot.wait(2000)

    def create_or_activate_window(self, window_key, url):
        """Cria uma nova janela ou ativa uma existente."""
        if window_key in self.window_handles:
            # Ativar janela existente
            try:
                print(f"Ativando janela: {window_key}")
                self.webbot.driver.switch_to.window(self.window_handles[window_key])
                return True
            except Exception as e:
                print(f"Erro ao ativar janela: {str(e)}")
                # Janela pode ter sido fechada, remover do dicionário
                del self.window_handles[window_key]
        
        # Criar nova janela
        try:
            print(f"Criando nova janela: {window_key} com URL: {url}")
            # Abrir nova aba usando JavaScript
            self.webbot.execute_javascript("window.open()")
            # Obter todas as janelas
            handles = self.webbot.driver.window_handles
            # A nova janela é a última na lista
            new_handle = handles[-1]
            # Alternar para a nova janela
            self.webbot.driver.switch_to.window(new_handle)
            # Navegar para a URL desejada
            self.webbot.browse(url)
            # Armazenar o handle da nova janela
            self.window_handles[window_key] = new_handle
            # Aguardar carregamento
            self.webbot.wait(2000)
            return True
        except Exception as e:
            print(f"Erro ao criar nova janela: {str(e)}")
            return False

    def ocr(self):
        """Extrai texto do elemento ocr usando OCR."""
        attempts = 0
        while attempts < self.max_attempts:
            # Lista de estratégias para encontrar o elemento
            strategies = [
                {"selector": '//*[@id="site-title"]/a[1]/img[1]', "by": By.XPATH, "desc": "xpath"},
                {"selector": "//'img'", "by": By.XPATH, "desc": "tag-fallback"},
            ]
            # Tenta cada estratégia
            for strategy in strategies:
                try:
                    print(f"Tentando encontrar elemento por {strategy['desc']}...")
                    element = self.webbot.find_element(strategy["selector"], strategy["by"])
                    # Capturar screenshot do elemento
                    screenshot_path = os.path.join(self.screenshots_folder, f'temp_ocr_screenshot.png')
                    element.screenshot(screenshot_path)
                    # Executar OCR no screenshot
                    extracted_text = pytesseract.image_to_string(Image.open(screenshot_path)).strip()
                    self.vars["ocr"] = extracted_text
                    print(f"Texto extraído com OCR: '{extracted_text}', salvo na variável ocr")
                    # Remover arquivo temporário
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                    return True
                except Exception as e:
                    print(f"Falha na estratégia {strategy['desc']}: {str(e)}")
                    continue  # Tentar próxima estratégia

            # Se chegou aqui, nenhuma estratégia funcionou nesta tentativa
            attempts += 1
            if attempts < self.max_attempts:
                print("Tentativa falhou. Tentando novamente após aguardar...")
                time.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
            else:
                print("Todas as tentativas falharam para o elemento.")
                return False

    def test(self):
        """Insere texto no elemento test."""
        attempts = 0
        while attempts < self.max_attempts:
            # Lista de estratégias para encontrar o elemento
            strategies = [
                {"selector": "username", "by": By.ID, "desc": "id"},
                {"selector": "username", "by": By.NAME, "desc": "name"},
                {"selector": '//*[@id="username"]', "by": By.XPATH, "desc": "xpath"},
                {"selector": "input#username", "by": By.CSS_SELECTOR, "desc": "css"},
                {"selector": "//'input'", "by": By.XPATH, "desc": "tag-fallback"},
            ]
            # Tenta cada estratégia
            for strategy in strategies:
                try:
                    print(f"Tentando encontrar elemento por {strategy['desc']}...")
                    element = self.webbot.find_element(strategy["selector"], strategy["by"])
                    element.clear()
                    # Verificar se a variável OCR existe antes de tentar usá-la
                    if "ocr" in self.vars:
                        # Usar o valor extraído diretamente
                        extracted_text = self.vars["ocr"]
                        print(f"Usando texto extraído por OCR: '{extracted_text}'")
                        element.send_keys(extracted_text)
                    else:
                        print("AVISO: Variável OCR não encontrada.")
                        # Fallback para input vazio
                        element.send_keys("")
                    print(f"Texto inserido com sucesso em ({strategy['desc']})")
                    return True
                except Exception as e:
                    print(f"Falha na estratégia {strategy['desc']}: {str(e)}")
                    continue  # Tentar próxima estratégia

            # Se chegou aqui, nenhuma estratégia funcionou nesta tentativa
            attempts += 1
            if attempts < self.max_attempts:
                print("Tentativa falhou. Tentando novamente após aguardar...")
                time.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
            else:
                print("Todas as tentativas falharam para o elemento.")
                return False

    def run(self):
        """Executa todas as interações em sequência."""
        try:
            # Iniciar navegação
            self.start_navigation()

            # Interagir
            if not self.ocr():
                print("Falha ao interagir com elemento. Interrompendo sequência.")
                return False
            # Aguardar um pouco após a interação
            time.sleep(0.5)

            # Interagir
            if not self.test():
                print("Falha ao interagir com elemento. Interrompendo sequência.")
                return False
            # Aguardar um pouco após a interação
            time.sleep(0.5)

            return True
        except Exception as e:
            print(f"Erro durante a execução: {str(e)}")
            return False
```

## 🛠️ Solução de Problemas
### Web Automation
❌ **Navegador não inicia**: Verifique a compatibilidade do driver.  
❌ **Elementos não capturados**: Verifique frames, iframes ou elementos dinâmicos.  
❌ **Erro no código**: Recapture os elementos se o site mudou.  

### Vision Automation
❌ **Elementos não encontrados**: Ajuste a precisão (`confidence`).  
❌ **OCR impreciso**: Expanda a região capturada e verifique a instalação do **Tesseract**.  

## 📚 Recursos Adicionais
- 📖 **Documentação do BotCity**: [Clique aqui](https://documentation.botcity.dev/)
- 🖥️ **Tesseract OCR**: [Repositório Oficial](https://github.com/tesseract-ocr/tesseract)

---
A **RPA Automation Suite** oferece ferramentas intuitivas para automação de processos, permitindo que usuários de todos os níveis criem soluções robustas sem necessidade de programação avançada! 🚀

