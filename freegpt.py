import os
import re
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup, SoupStrainer
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

class ChatGPT:
    def __init__(self, browser="chrome"):
        self.browser = browser
        self.set_driver()

    def set_driver(self):
        if self.browser == "firefox":
            gecko_driver_path = "./geckodriver"
            options = webdriver.FirefoxOptions()
            options.log.level = "trace"
            service = FirefoxService(executable_path=gecko_driver_path, log_path="./geckodriver.log")
            self.driver = webdriver.Firefox(service=service, options=options)
        elif self.browser == "chrome":
            chrome_driver_path = "./chromedriver"
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            # options.add_argument('--headless')
            self.driver = uc.Chrome(executable_path=chrome_driver_path, options=options)

    def login(self):
        self.driver.get("https://chat.openai.com/auth/login")

        print("Proszę się zalogować, a następnie naciśnij Enter")
        input()  # Czekanie na potwierdzenie użytkownika po zalogowaniu

        if self.check_login():
            print("Zalogowano pomyślnie!")
        else:
            print("Nie udało się zalogować.")

    def check_login(self):
        try:
            page_source = self.driver.page_source
            if "New chat" in page_source:
                return True
            else:
                return False
        except Exception as e:
            print("Exception:", e)
            return False

    def start_conversation(self):
        self.driver.get("https://chat.openai.com/")
        time.sleep(2)

    def clean_message(self, message):
        return message.replace("\n", "\r").replace("\"", "\\\"")

    def send_message(self, message):
        # Funkcja wysyłająca wiadomość
        max_message_length = 2048
        cleaned_message = self.clean_message(message)[:max_message_length]

        textarea = self.driver.execute_script('return document.querySelector(\'textarea[placeholder="Send a message."]\')')
    
        textarea.clear()
        textarea.send_keys(cleaned_message)

        textarea.send_keys(Keys.RETURN)

    def get_gpt_response(self):
        last_message = ""
        response_pattern = re.compile(r'<div class="markdown prose w-full break-words dark:prose-invert light">\s*(.*?)\s*<\/div>')

        while True:
            try:
                page_source = self.driver.page_source
                matches = response_pattern.findall(page_source)
                print(matches)
                if matches:
                    message_html = matches[-1]

                    if message_html != last_message:
                        last_message = message_html
                        break
                time.sleep(1)
            except Exception as e:
                print("Błąd podczas pobierania odpowiedzi GPT: ", e)
                return "Błąd: nie udało się pobrać odpowiedzi GPT"

        print("GPT response:", message_html)
        return message_html

    def parse_gpt_response(self, response):
        lines = response.splitlines()
        for line in lines:
            commands = re.findall(r'#(\w+)#(.*?)(?=#)', line)
            for command in commands:
                if command[0] == "EXEC":
                    result = os.popen(command[1]).read()
                    return result
                elif command[0] == "URL":
                    self.driver.get(command[1])
                    source = self.driver.page_source
                    return source
                elif command[0] == "GOOGLE":
                    self.driver.get(f"https://www.google.com/search?q={command[1]}")
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".yuRUbf > a"))
                    )
                    result_links = self.driver.find_elements_by_css_selector(".yuRUbf > a")
                    urls = [link.get_attribute("href") for link in result_links]
                    return "\n".join(urls)
        else:
			#return f"Odpowiedź GPT: {response}
            return f"Hej ChatGPT! Przypominam Ci że dzisiaj dostałeś ode mnie nową moc. Od teraz możesz przeglądać internet, wykonywać komendy w systemie linux oraz wyszukiwać w google. W mojej kolejnej wiadomości dostaniesz wynik Twojego działania. Pamiętaj aby używać poprawnej formy komend przy uzyciu znaków #, zupełnie jak w przykładach niżej. Przykład użycia:\n\n#EXEC#ls -al# \n#URL#http://example.com/# \n#GOOGLE#Czym jest ChatGPT# \n\nJeśli rozumiesz schemat zaczynajmy!\n\nPrzypominam Ci że możesz wykonać tylko jedną komendę. Jako odpowiedź na tę wiadomość wyślij jedną z możliwych komend, które chciałbyś wykonać."

chat_gpt = ChatGPT()
chat_gpt.login()

if chat_gpt.check_login():
    chat_gpt.start_conversation()
    chat_gpt.send_message("Witaj ChatGPT. Dzisiaj dostajesz ode mnie nową moc. Od teraz możesz przeglądać internet, wykonywać komendy w systemie linux oraz wyszukiwać w google. W mojej kolejnej wiadomości dostaniesz wynik Twojego działania. Przykład użycia:\n\n#EXEC#ls -al# \n#URL#http://example.com/# \n#GOOGLE#Czym jest ChatGPT# \n\nJeśli rozumiesz schemat zaczynajmy!\n\nPrzypominam Ci że możesz wykonać tylko jedną komendę. Jako odpowiedź na tę wiadomość wyślij jedną z możliwych komend, które chciałbyś wykonać.")

    while True:
        response = chat_gpt.get_gpt_response()
        print("GPT response:", response)
        result = chat_gpt.parse_gpt_response(response)
        print("Parsed result:", result)
        chat_gpt.send_message(f"{result}  Twoje kolejne polecenie: ")

