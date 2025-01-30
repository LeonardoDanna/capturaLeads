from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import tkinter as tk
from tkinter import simpledialog

#Versão do deepseek

# Função para ler estabelecimentos já capturados de um arquivo CSV
def ler_estabelecimentos_csv():
    try:
        with open('leads.csv', mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            return set(row[0] for row in reader)  # Retorna um conjunto de nomes
    except FileNotFoundError:
        return set()  # Retorna um conjunto vazio se o arquivo não existir

# Função para salvar dados no arquivo CSV
def salvar_no_csv(dados):
    with open('leads.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(dados)  # Escreve cada linha no CSV

# Função para obter cidade e tipo de estabelecimento do usuário
def obter_informacoes_usuario():
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal

    cidade = simpledialog.askstring("Entrada", "Digite a cidade:")
    tipo_estabelecimento = simpledialog.askstring("Entrada", "Digite o tipo de estabelecimento:")
    
    root.destroy()  # Fecha a janela após a coleta de dados
    return cidade, tipo_estabelecimento

# Função para enviar mensagem no WhatsApp
def enviar_mensagem_whatsapp(telefone, mensagem):
    try:
        print(f"Iniciando envio de mensagem para {telefone}...")
        driver.get(f'https://web.whatsapp.com/send?phone={telefone}')
        print("Aguardando carregamento do WhatsApp Web...")

        # Espera até que a caixa de texto esteja presente na página
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        print("Caixa de texto localizada. Digitando a mensagem...")

        caixa_de_texto = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        caixa_de_texto.send_keys(mensagem)
        caixa_de_texto.send_keys(Keys.ENTER)
        print("Mensagem enviada com sucesso!")
        time.sleep(2)
    except Exception as e:
        print(f"Erro ao enviar mensagem para {telefone}: {e}")

# Configurações do Selenium
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')  # Inicia o navegador maximizado
driver = webdriver.Chrome(options=options)

# Obtém cidade e tipo de estabelecimento do usuário
cidade, tipo_estabelecimento = obter_informacoes_usuario()

try:
    # Abre o Google Maps
    driver.get("https://www.google.com/maps")

    # Aguarda o carregamento da página
    time.sleep(3)

    # Encontra o campo de busca e insere o tipo de estabelecimento e a cidade
    search_box = driver.find_element(By.XPATH, '//input[@id="searchboxinput"]')
    search_box.send_keys(f"{tipo_estabelecimento} em {cidade}")
    search_box.send_keys(Keys.RETURN)

    # Aguarda o carregamento dos resultados
    time.sleep(5)

    # Encontra o elemento rolável
    scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

    # Função para rolar a página
    def scroll_to_load_all_reviews(scrollable_div):
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(2)  # Espera para o conteúdo carregar
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            if new_height == last_height:
                break  # Sai do loop se não houver mais novos elementos
            last_height = new_height

    scroll_to_load_all_reviews(scrollable_div)

    # Coletar links dos resultados
    resultados = driver.find_elements(By.CLASS_NAME, "Nv2PK")

    if not resultados:
        print("Nenhum resultado encontrado.")
        driver.quit()
        exit()

    links_detalhes = []
    for resultado in resultados:
        try:
            link = resultado.find_element(By.TAG_NAME, "a").get_attribute("href")
            links_detalhes.append(link)
        except Exception as e:
            print(f"Erro ao capturar link: {e}")

    estabelecimentos_capturados = ler_estabelecimentos_csv()  # Ler estabelecimentos já capturados

    # Mensagem personalizada para enviar
    mensagem_promocional = "Olá, somos da Loja X! Temos uma promoção especial para você: 20% de desconto em toda a loja. Venha conferir!"

    for link in links_detalhes:
        try:
            driver.get(link)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
            )

            nome = driver.find_element(By.CLASS_NAME, "DUwDvf").text

            # Verificar se o nome do estabelecimento já foi capturado
            if nome in estabelecimentos_capturados:
                print(f"Estabelecimento {nome} já capturado. Pulando...")
                continue

            # Verificar se o telefone já foi capturado
            telefone_element = driver.find_elements(By.XPATH, "//button[contains(@data-tooltip, 'telefone')]")
            if telefone_element:
                telefone = telefone_element[0].text.replace("\n", "").replace("", "")
                if telefone != "Não disponível":
                    # Enviar mensagem pelo WhatsApp
                    enviar_mensagem_whatsapp(telefone, mensagem_promocional)
            else:
                telefone = "Não disponível"

            print(f"Capturado: {nome} - {telefone}")  # Log para depuração
            
            # Salvar no CSV imediatamente após a captura
            salvar_no_csv((nome, telefone))
            estabelecimentos_capturados.add(nome)  # Adicionar o nome à lista de capturados

        except Exception as e:
            print(f"Erro ao processar um resultado: {e}")

    print("Leads capturados e mensagens enviadas com sucesso!")

except Exception as e:
    print(f"Erro: {e}")

finally:
    driver.quit()  # Fecha o navegador após a execução

# Função para formatar o arquivo CSV
def formatar_leads(nome_arquivo):
    with open(nome_arquivo, 'r', encoding='utf-8') as file:
        # Lê o conteúdo do arquivo como uma lista de linhas
        reader = csv.reader(file)
        linhas = list(reader)

    # Verifica e adiciona o cabeçalho se necessário
    if not linhas or linhas[0] != ['nome', 'numero']:
        linhas.insert(0, ['nome', 'numero'])

    # Divide as linhas em categorias (ignora o cabeçalho)
    com_numero_prioritario = []
    com_numero_comum = []
    sem_numero = []

    for linha in linhas[1:]:
        # Verifica se a linha tem nome e número válidos
        if len(linha) < 2 or not linha[0].strip() or not linha[1].strip():
            continue  # Ignora linhas inválidas

        nome, numero = linha
        if numero.startswith('(19) 9'):
            com_numero_prioritario.append(linha)
        elif numero == 'Não disponível':
            sem_numero.append(linha)
        else:
            com_numero_comum.append(linha)

    # Ordena cada categoria por ordem alfabética do nome
    com_numero_prioritario.sort(key=lambda x: x[0].lower())
    com_numero_comum.sort(key=lambda x: x[0].lower())
    sem_numero.sort(key=lambda x: x[0].lower())

    # Reorganiza as linhas
    linhas_ordenadas = [['nome', 'numero']] + com_numero_prioritario + com_numero_comum + sem_numero

    # Escreve as linhas reorganizadas de volta no arquivo
    with open(nome_arquivo, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(linhas_ordenadas)

# Exemplo de uso
formatar_leads('leads.csv')
print("Arquivo leads.csv formatado com sucesso.")