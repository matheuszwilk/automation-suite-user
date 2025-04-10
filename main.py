from botcity.web import WebBot, Browser, By
from botcity.web.browsers.edge import default_options

class AutomationBot:
    def __init__(self, url, credentials_file_path):
        self.url = url
        self.credentials_file_path = credentials_file_path
        self.webbot = None

    def open_website(self):
        self.webbot = WebBot()
        self.webbot.headless = False
        self.webbot.browser = Browser.EDGE
        self.webbot.driver_path = "msedgedriver.exe"
        
        # Configure options BEFORE browsing
        # Get default options
        options = default_options(
            headless=self.webbot.headless,
            download_folder_path=self.webbot.download_folder_path,
            user_data_dir=None
        )
        
        # Add your custom arguments
        options.add_argument("--disable-gpu")  # Evita erros gráficos
        options.add_argument("--log-level=3")  # Reduz o nível de logs
        
        # Add this option to show the controlled by automation message
        options.add_experimental_option("excludeSwitches", [])
        
        # Update the webbot options
        self.webbot.options = options
        
        # Now open the browser with these options
        self.webbot.browse(self.url)
        self.webbot.maximize_window()
        # self.webbot.options.add_argument("--headless")  # Para rodar sem abrir o navegador

    # def start(self):
    #     functions = PracticetestautomationFunctions(self.webbot)
    #     functions.run()
    
    # def clickImages(self):
    #     """
    #     Wrapper para chamar main.click_images. Isto se torna um dos passos do fluxo.
    #     """
    #     main.click_images(main.tasks)

    def run(self):
        while True:
            try:
                self.open_website()
                self.start()

                print("Terminou")
                input()
            except Exception as e:
                raise Exception("Ocorreu um erro na função run:", e)
            continue


if __name__ == '__main__':
    bot = AutomationBot("https://practicetestautomation.com/practice-test-exceptions/", "credential.txt")
    bot.run()
