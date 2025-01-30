import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurações do Selenium
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')  # Inicia o navegador maximizado
driver = webdriver.Chrome(options=options)

# Função para aguardar elemento
def aguardar_elemento(xpath, tempo=30):
    try:
        elemento = WebDriverWait(driver, tempo).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return elemento
    except Exception as e:
        print(f"Erro ao aguardar elemento ({xpath}): {e}")
        return None

# Função para enviar mensagem
def enviar_mensagem(numero, mensagem):
    url = f"https://web.whatsapp.com/send?phone={numero}&text={mensagem}"
    driver.get(url)
    print(f"Carregando conversa para o número {numero}...")
    time.sleep(20)  # Aumente o tempo de espera para carregar a conversa

    # Verificar e clicar no botão de enviar
    enviar_button = aguardar_elemento('//button[@data-testid="compose-btn-send"]')
    if enviar_button:
        try:
            enviar_button.click()
            print(f"Mensagem enviada para {numero}.")
            time.sleep(5)  # Tempo para o envio da mensagem
        except Exception as e:
            print(f"Erro ao clicar no botão de enviar para {numero}: {e}")
    else:
        print(f"Erro: Botão de enviar não encontrado para o número {numero}.")

# Carregar dados do CSV
csv_file = 'leads.csv'  # Substitua pelo caminho do seu arquivo CSV
mensagem_base = "Olá {nome}"

try:
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for linha in reader:
            nome = linha['nome']
            telefone = linha['telefone']
            mensagem = mensagem_base.format(nome=nome)
            enviar_mensagem(telefone, mensagem)
except FileNotFoundError:
    print(f"Arquivo CSV '{csv_file}' não encontrado. Verifique o caminho.")

# Fechar o navegador após o envio
driver.quit()
