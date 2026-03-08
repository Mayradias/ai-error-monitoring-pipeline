import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    TimeoutException
)

# ================= CONFIG =================

CHROMEDRIVER_PATH = "YOUR_CHROMEDRIVER_PATH"
PROFILE_PATH =  "YOUR_BROWSER_PROFILE"

URL_BASE = "INTERNAL_PORTAL_URL"
ARQUIVO_SAIDA = "motivos_rejeicao.txt"

SLEEP_NAV = 0.6

# =========================================


# ================= DRIVER =================

service = Service(CHROMEDRIVER_PATH)

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={PROFILE_PATH}")
options.add_argument("--profile-directory=Default")

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 40)

driver.get(URL_BASE)


# ================= FUNÇÕES =================

def esperar_tabela_estavel():
    """Espera DOM realmente estabilizar (Angular)"""
    time.sleep(0.8)
    wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr"))
    )


def clicar(xpath, tentativas=3):
    for _ in range(tentativas):
        try:
            el = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                el
            )
            time.sleep(0.3)
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            el.click()
            return

        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
            TimeoutException
        ):
            time.sleep(0.6)

    el = driver.find_element(By.XPATH, xpath)
    driver.execute_script("arguments[0].click();", el)


def ir_para_pagina(pagina):
    if pagina <= 1:
        return
    clicar(f"//button[normalize-space()='{pagina}']")
    esperar_tabela_estavel()


def ir_para_proxima_pagina(pagina):
    proxima = str(pagina + 1)
    try:
        clicar(f"//button[normalize-space()='{proxima}']")
        esperar_tabela_estavel()
        return True
    except:
        return False


# ================= INSTRUÇÕES =================

print("\n⚠ PASSOS MANUAIS ⚠")
print("1 Faça LOGIN")
print("2 Vá em DOCUMENTOS")
print("3 Filtre REJEITADOS")
print("4 Clique em CONSULTAR\n")

input(" Quando a LISTA estiver visível, pressione ENTER...")


with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
    f.write("RELATÓRIO – MOTIVOS DE REJEIÇÃO\n\n")


contador_total = 0
pagina_atual = 1


# ================= LOOP PRINCIPAL =================

try:
    while True:

        processados = set()

        clicar("//a[contains(.,'Documentos')]")
        time.sleep(SLEEP_NAV)

        clicar("//button[contains(.,'Consultar')]")
        esperar_tabela_estavel()

        ir_para_pagina(pagina_atual)

        print(f"\n📄 Página {pagina_atual}")

        # ===== PROCESSA SEMPRE RELOCALIZANDO =====
        while True:

            linhas = driver.find_elements(By.XPATH, "//table//tbody/tr")

            linha_pid = None

            for l in linhas:
                texto = l.text.strip()

                if (
                    not texto
                    or "Carregando" in texto
                    or "Nenhum" in texto
                ):
                    continue

                pid = l.find_element(By.XPATH, ".//td[1]").text.strip()

                if pid not in processados:
                    linha_pid = pid
                    break

            if not linha_pid:
                print("✔ Página concluída")
                break

            print(f"➡ Protocolo {linha_pid}")
            processados.add(linha_pid)

            # 🔥 relocaliza linha pelo PID (anti-stale definitivo)
            linha = driver.find_element(
                By.XPATH,
                f"//tr[td[1][contains(.,'{linha_pid}')]]"
            )

            botoes = linha.find_elements(By.XPATH, ".//button")
            if len(botoes) < 3:
                continue

            botoes[2].click()

            clicar("//button[contains(.,'Rejeitar')]")

            campo = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//*[normalize-space()='Motivo Rejeição']/following::textarea[1]")
                )
            )

            wait.until(lambda d: campo.get_attribute("value").strip() != "")
            motivo = campo.get_attribute("value").strip()

            with open(ARQUIVO_SAIDA, "a", encoding="utf-8") as f:
                f.write(f"Protocolo {linha_pid}\n{motivo}\n{'-'*60}\n")

            contador_total += 1
            print("📄 Motivo extraído")

            clicar("//button[contains(.,'Cancelar')]")
            clicar("//a[contains(.,'Documentos')]")
            clicar("//button[contains(.,'Consultar')]")
            esperar_tabela_estavel()

            ir_para_pagina(pagina_atual)

        if ir_para_proxima_pagina(pagina_atual):
            pagina_atual += 1
        else:
            print( "Última página alcançada")
            break


except KeyboardInterrupt:
    print("\nInterrompido pelo usuário")

finally:
    print("\nRESUMO FINAL")
    print(f"Protocolos processados: {contador_total}")
    print(f"Última página: {pagina_atual}")
    print(f"Arquivo: {ARQUIVO_SAIDA}")
    driver.quit()

