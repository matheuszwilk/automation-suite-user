# Import necessary libraries and modules
from botcity.web import WebBot, Browser, By
import pytesseract
import os
from PIL import Image
from botcity.web.browsers.ie import default_options

# Define a class named AutomationBot to encapsulate the automation logic
class AutomationBot:
    def __init__(self, url, credentials_file_path):
        self.url = url
        self.credentials_file_path = credentials_file_path
        self.webbot = None

    def open_website(self):
        # Create a WebBot instance and configure it for Internet Explorer
        self.webbot = WebBot()
        self.webbot.headless = False
        self.webbot.browser = Browser.IE
        self.webbot.driver_path = "IEDriverServer.exe"

        # Set additional options for Internet Explorer
        ie_options = default_options()
        ie_options.add_additional_option("ie.edgechromium", True)
        ie_options.add_additional_option("ignoreProtectedModeSettings", True)
        ie_options.add_additional_option("requireWindowFocus", True)
        ie_options.add_additional_option("ignoreZoomSetting", True)
        ie_options.add_additional_option("nativeEvents", True)
        # Important: Change to the path where your Microsoft Edge is installed
        ie_options.add_additional_option("ie.edgepath", "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe") 
        self.webbot.options = ie_options

        # Open the specified URL and maximize the window
        self.webbot.browse(self.url)
        self.webbot.maximize_window()

    def read_credentials(self):
        # Read credentials from a file and return them
        with open(self.credentials_file_path, "r") as file:
            username = file.readline().strip()
            password = file.readline().strip()
            employee = file.readline().strip()
            date = file.readline().strip()
        return username, password, employee, date

    def login(self, username, password):
        # Perform the login process using JavaScript to interact with the web elements
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            username_field = self.webbot.find_element(selector='USER', by=By.ID)
            username_field.click()
            username_field.send_keys(username)
            password_field = self.webbot.find_element(selector='LDAPPASSWORD', by=By.ID)
            password_field.click()
            password_field.send_keys(password)
            findOTP = """document.getElementById('OTP').click();"""
            self.webbot.execute_javascript(findOTP)

    def fill_otp_form(self, password):
        # Fill out the OTP form using JavaScript and switch to a new tab
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            new_tab = self.webbot.get_tabs()[1]
            self.webbot.activate_tab(new_tab)
            password_field = """document.getElementById('pw').click();
            document.getElementById('pw').value = '""" + password + """';"""
            self.webbot.execute_javascript(password_field)
            mybtn = """document.getElementById('myButton').click();"""
            self.webbot.execute_javascript(mybtn)
            new_tab = self.webbot.get_tabs()[1]
            self.webbot.activate_tab(new_tab)
            self.webbot.close_page()
            self.webbot.create_tab("http://otpauth.lge.com:8090/selfservice/TempPasswordRequestPcode.jsp?lang=eng")

    def fill_request_form(self, employee, date):
        # Fill out the request form and handle CAPTCHA using Python and JavaScript
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            employee_field = """document.getElementById('bizidE').click();
            document.getElementById('bizidE').value = '""" + employee + """';"""
            self.webbot.execute_javascript(employee_field)
            employee_field = """document.getElementById('pcodeE').click();
            document.getElementById('pcodeE').value = '""" + date + """';"""
            self.webbot.execute_javascript(employee_field)

            self.webbot.wait(3000)

            if not os.path.exists('captchas'):
                os.mkdir("captchas")

            img_path = './captchas/img_screen.png'
            selector_submit_captcha = "#form1 > div.eng > table > tbody > tr:nth-child(7) > td > input[type=button]:nth-child(1)"

            self.webbot.wait(3000)
            code = """document.getElementById('photo_imageE');"""
            elem_captcha = self.webbot.execute_javascript(code)
            elem_captcha = self.webbot.find_element("photo_imageE", By.ID)
            recaptcha = """document.getElementById('answerE');"""
            elem_recaptcha = self.webbot.execute_javascript(recaptcha)
            elem_recaptcha = self.webbot.find_element("answerE", By.ID)
            elem_captcha.screenshot(img_path)

            # Use pytesseract to extract text from the CAPTCHA image
            # Important: Change the path where your Tesseract-OCR is installed.
            pytesseract.pytesseract.tesseract_cmd = "C:/Users/matheus.pereira/AppData/Local/Programs/Tesseract-OCR/tesseract.exe" 
            resp_captcha = pytesseract.image_to_string(img_path)
            resp_captcha = str(resp_captcha)
            resp_captcha = resp_captcha.lower()
            resp_captcha = resp_captcha.translate({ord(i): None for i in ' '})

            self.webbot.wait(2000)
            elem_recaptcha.click()
            elem_recaptcha.send_keys(resp_captcha)
            self.webbot.wait(1000)
            self.webbot.find_element(selector_submit_captcha, By.CSS_SELECTOR).click()
            self.webbot.wait(2000)

            if self.webbot.get_js_dialog() is not None:
                dialog = self.webbot.get_js_dialog()
                dialog.accept()
                self.fill_request_form(employee, date)
            else:
                self.webbot.close_page()

    def temporary_otp_form(self):
        # Get the temporary OTP from the page and enter it into the form
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            self.webbot.wait(1000)
            getOTP = """document.getElementById('loadingE').textContent;"""
            temporay = self.webbot.execute_javascript(getOTP)
            temporay = self.webbot.find_element(selector='loadingE', by=By.ID).text
            temporays = str(temporay)
            self.webbot.close_page()

        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            self.webbot.wait(1000)
            new_tabs = self.webbot.get_tabs()[0]
            self.webbot.activate_tab(new_tabs)
            password_field = """document.getElementById('OTPPASSWORD').click();
                document.getElementById('OTPPASSWORD').value = '""" + temporays + """';"""
            self.webbot.execute_javascript(password_field)
            self.webbot.enter()

    def entrar_gqis(self):
        # Perform actions to enter the GQIS system
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            self.webbot.wait(1000)
            enter_gqis = """document.querySelector('a[title="GQIS"]').click();"""
            self.webbot.execute_javascript(enter_gqis)
            new_tab2 = self.webbot.get_tabs()[0]
            self.webbot.activate_tab(new_tab2)
    
    def entrar_cdrByProduct(self):
        self.webbot.wait(1000)
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            new_tab2 = self.webbot.get_tabs()[1]
            self.webbot.activate_tab(new_tab2)
            CDR_By_Product = """parent['topFrame'].document.getElementById('subItem0').click();"""
            self.webbot.execute_javascript(CDR_By_Product)

        self.webbot.wait(1000)
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            Prod_Corp = """parent['mainFrame'].document.getElementById('PA').click();"""
            self.webbot.execute_javascript(Prod_Corp)
            self.webbot.wait(10000)

        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            new_tab2 = self.webbot.get_tabs()[2]
            self.webbot.activate_tab(new_tab2)

            findProd_Corp = self.webbot.find_element("//td[text()='Manaus']", By.XPATH)
            self.webbot.wait_for_element_visibility(element=findProd_Corp, visible=True, waiting_time=20000)
            clickFindProd_Corp = self.webbot.find_element(selector="//td[text()='Manaus']", by=By.XPATH) 
            clickFindProd_Corp.click()

            btnOK = self.webbot.find_element('//a[@class="okBtn" and @onclick="onOkBtnClicked();"]', By.XPATH)
            self.webbot.wait_for_element_visibility(element=btnOK, visible=True, waiting_time=20000)
            clickBtnOK = self.webbot.find_element(selector='//a[@class="okBtn" and @onclick="onOkBtnClicked();"]', by=By.XPATH)
            clickBtnOK.click()

        with self.webbot.wait_for_new_page(waiting_time=20000, activate=True):
            new_tab = self.webbot.get_tabs()[1]
            self.webbot.activate_tab(new_tab)
            changeDate = """parent['mainFrame'].document.getElementById('basicMonthFr').selectedIndex = 0;"""
            self.webbot.execute_javascript(changeDate)
            racWSales = """parent['mainFrame'].document.getElementById('racSalesWeight').click(); """
            self.webbot.execute_javascript(racWSales)
        
        # Choose product or division
        self.webbot.wait(1000)
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            Prod_Corp = """parent['mainFrame'].document.getElementById('PR').click();"""
            self.webbot.execute_javascript(Prod_Corp)
            self.webbot.wait(10000)

        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            new_tab2 = self.webbot.get_tabs()[2]
            self.webbot.activate_tab(new_tab2)

        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            btnView = self.webbot.find_element('//div[@class="dhx_toolbar_btn def" and @title="View Aggregation"]', By.XPATH)
            self.webbot.wait_for_element_visibility(element=btnView, visible=True, waiting_time=20000)
            clickbtnView = self.webbot.find_element(selector='//div[@class="dhx_toolbar_btn def" and @title="View Aggregation"]', by=By.XPATH)
            clickbtnView.click()

        with self.webbot.wait_for_new_page(waiting_time=20000, activate=True): 
            self.webbot.wait(12000)
            findProd_Corp = self.webbot.find_element("//td[text()='*QP(D.1_SRAC_Inverter 인버터 벽걸이형)']", By.XPATH)
            self.webbot.wait_for_element_visibility(element=findProd_Corp, visible=True, waiting_time=20000)
            clickFindProd_Corp = self.webbot.find_element(selector="//td[text()='*QP(D.1_SRAC_Inverter 인버터 벽걸이형)']", by=By.XPATH) 
            clickFindProd_Corp.click()

        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            self.webbot.wait(2000)
            btnOK = self.webbot.find_element('//a[@class="okBtn" and @onclick="onOkBtnClicked();"]', By.XPATH)
            self.webbot.wait_for_element_visibility(element=btnOK, visible=True, waiting_time=20000)
            clickBtnOK = self.webbot.find_element(selector='//a[@class="okBtn" and @onclick="onOkBtnClicked();"]', by=By.XPATH)
            clickBtnOK.click()

        # Search for the data
        with self.webbot.wait_for_new_page(waiting_time=10000, activate=True):
            new_tab = self.webbot.get_tabs()[1]
            self.webbot.activate_tab(new_tab)
            btnSearch = """parent['mainFrame'].document.getElementById('imgShow').click();"""
            self.webbot.execute_javascript(btnSearch)
            self.webbot.wait(10000)

    def openExcel(self):
        self.deskbot = DesktopBot()
        print("Iniciou")
        if not self.deskbot.find( "excelDL", matching=0.97, waiting_time=10000):
            print("AA")
        self.deskbot.click()
        input()

    def run(self):
        while True:
            try:
                # Perform the automation steps in sequence
                self.open_website()
                username, password, employee, date = self.read_credentials()
                self.login(username, password)
                self.fill_otp_form(password)
                self.fill_request_form(employee, date)
                self.temporary_otp_form()
                self.entrar_gqis()
                try:
                    self.entrar_cdrByProduct()
                    self.webbot.wait(4000)
                    self.openExcel()
                except Exception as e:
                    raise Exception("Ocorreu um erro na função entrar_cdrByProduct:", e)
                continue
            except Exception as e:
                raise Exception("Ocorreu um erro na função run:", e)
            continue

# Entry point of the script
if __name__ == '__main__':
    # Create an instance of the AutomationBot and run the automation process
    bot = AutomationBot("https://sso.lge.com/", "credential.txt")
    bot.run()
