#!/usr/bin/env python3

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ================= CONFIG =================
PROFILE_PATH = r"C:\selenium-profile"
URL_BASE = "https://URL_DO_PORTAL"
SLEEP_NAV = 0.5
WAIT_TIMEOUT = 40
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SAIDA = os.path.join(BASE_DIR, "protocolos_aprovados.txt")
# =========================================

# ================= DRIVER =================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={PROFILE_PATH}")
options.add_argument("--profile-directory=Default")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, WAIT_TIMEOUT)
driver.get(URL_BASE)

# ================= FUNÇÕES =================
def clicar(xpath):
    el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.3)
    el.click()

def ir_para_pagina(p):
    if p <= 1:
        return
    clicar(f"//button[normalize-space()='{p}']")
    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr")))

def ir_para_proxima_pagina(p):
    proxima = str(p + 1)
    try:
        clicar(f"//button[normalize-space()='{proxima}']")
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr")))
        return True
    except:
        return False

def scroll_tabela():
    driver.execute_script("document.querySelector('table tbody').scrollIntoView(false);")
    time.sleep(0.3)

# ================= INSTRUÇÕES =================
print("\n⚠ PASSOS MANUAIS ⚠")
print("1 Faça LOGIN")
print("2 Vá em DOCUMENTOS")
print("3 Filtre por APROVADOS")
print("4 Clique em CONSULTAR\n")
input("👉 Quando a LISTA estiver visível, pressione ENTER...")

# ================= EXTRAÇÃO =================
pagina_atual = 1
total_secoes = 0
protocolos_unicos = set()  # 🔹 controla duplicados

with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:

    print("\n🚀 Iniciando extração...\n")

    while True:
        if pagina_atual > 1:
            ir_para_pagina(pagina_atual)

        print(f"📄 Página {pagina_atual}")
        scroll_tabela()

        linhas = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr")))
        print(f"Linhas encontradas nesta página: {len(linhas)}")

        encontrados_na_pagina = 0
        for linha in linhas:
            texto = linha.text.strip()
            if not texto or "Carregando" in texto or "Nenhum" in texto:
                continue
            try:
                protocolo = linha.find_element(By.XPATH, ".//td[1]").text.strip()
                secao = linha.find_element(By.XPATH, ".//td[2]").text.strip() 
                situacao = linha.find_element(By.XPATH, ".//td[3]").text.strip()
                data = linha.find_element(By.XPATH, ".//td[6]").text.strip()
            except:
                continue

            # salva no arquivo
            f.write(f"Protocolo: {protocolo} | Seção: {secao} | Situação: {situacao} | Data: {data}\n")

            # contagem
            total_secoes += 1
            protocolos_unicos.add(protocolo)

            encontrados_na_pagina += 1

        print(f"   ➕ Seções nesta página: {encontrados_na_pagina}")
        print(f"   📊 Total de seções: {total_secoes}")
        print(f"   🧾 Protocolos únicos até agora: {len(protocolos_unicos)}")

        if ir_para_proxima_pagina(pagina_atual):
            pagina_atual += 1
            time.sleep(SLEEP_NAV)
        else:
            print("\n🏁 Última página alcançada")
            break

print("\n📊 EXTRAÇÃO FINALIZADA")
print(f"✔ Total de seções: {total_secoes}")
print(f"🧾 Total de protocolos únicos: {len(protocolos_unicos)}")
print(f"💾 Dados salvos em '{ARQUIVO_SAIDA}'")

driver.quit()