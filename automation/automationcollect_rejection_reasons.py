import time
import os
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
from webdriver_manager.chrome import ChromeDriverManager

# ================= CONFIG =================

PROFILE_PATH = r"C:\selenium-profile"
URL_BASE = "https://URL_DO_PORTAL"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SAIDA = os.path.join(BASE_DIR, "motivos_rejeicao.txt")
SLEEP_NAV = 0.6
WAIT_TIMEOUT = 40

# ==========================================

# ================= DRIVER =================

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"--user-data-dir={PROFILE_PATH}")
options.add_argument("--profile-directory=Default")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, WAIT_TIMEOUT)
driver.get(URL_BASE)

# ==========================================

# ================= FUNÇÕES =================

def esperar_tabela_estavel():
    time.sleep(0.8)
    wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//table//tbody/tr"))
    )


def clicar(xpath, tentativas=3):
    for _ in range(tentativas):
        try:
            el = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", el
            )
            time.sleep(0.3)
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            el.click()
            return True
        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
            TimeoutException
        ):
            time.sleep(0.6)
    return False


def ir_para_pagina(pagina):
    if pagina <= 1:
        return
    clicar(f"//button[normalize-space()='{pagina}']")
    esperar_tabela_estavel()


def ir_para_proxima_pagina(pagina):
    proxima = str(pagina + 1)
    botoes = driver.find_elements(
        By.XPATH, f"//button[normalize-space()='{proxima}']"
    )
    if not botoes:
        return False
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", botoes[0]
    )
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", botoes[0])
    esperar_tabela_estavel()
    return True


def obter_proximo_pid(processados):
    """
    Relocaliza as linhas da tabela e retorna o próximo PID
    ainda não processado. Retorna None se a página está completa.
    Usa relocalização por PID para evitar StaleElementReferenceException.
    """
    linhas = driver.find_elements(By.XPATH, "//table//tbody/tr")
    for linha in linhas:
        texto = linha.text.strip()
        if not texto or "Carregando" in texto or "Nenhum" in texto:
            continue
        try:
            pid = linha.find_element(By.XPATH, ".//td[1]").text.strip()
            if pid and pid not in processados:
                return pid
        except StaleElementReferenceException:
            continue
    return None


def relocar_linha(pid):
    """Relocaliza a linha pelo PID — evita StaleElement após navegação."""
    return driver.find_element(
        By.XPATH, f"//tr[td[1][contains(.,'{pid}')]]"
    )

# ==========================================

# ================= INSTRUÇÕES =================

print("\n⚠ PASSOS MANUAIS ⚠")
print("1. Faça LOGIN")
print("2. Vá em DOCUMENTOS")
print("3. Filtre por REJEITADOS")
print("4. Clique em CONSULTAR\n")
input("👉 Quando a LISTA estiver visível, pressione ENTER...")

# ==========================================

# ================= ARQUIVO DE SAÍDA =================

with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
    f.write("RELATÓRIO – MOTIVOS DE REJEIÇÃO\n\n")

# ==========================================

# ================= LOOP PRINCIPAL =================

contador_total = 0
pagina_atual = 1
protocolos_unicos = set()

try:
    while True:

        processados = set()  # PIDs já processados nesta página

        # Renavega para garantir estado limpo da tabela
        clicar("//a[contains(.,'Documentos')]")
        time.sleep(SLEEP_NAV)
        clicar("//button[contains(.,'Consultar')]")
        esperar_tabela_estavel()
        ir_para_pagina(pagina_atual)

        print(f"\n📄 Página {pagina_atual}")

        # ===== LOOP DA PÁGINA =====
        while True:

            # Obtém próximo PID não processado (relocaliza a cada iteração)
            pid = obter_proximo_pid(processados)

            if not pid:
                print("✔ Página concluída")
                break

            print(f"➡ Protocolo {pid}")
            processados.add(pid)
            protocolos_unicos.add(pid)

            # Relocaliza a linha pelo PID
            try:
                linha = relocar_linha(pid)
                secao = linha.find_element(By.XPATH, ".//td[2]").get_attribute("innerText").strip()
                data_protocolo = linha.find_element(By.XPATH, ".//td[6]").text.strip()
            except StaleElementReferenceException:
                print("⚠ Linha ficou stale ao ler dados — pulando")
                continue

            # Abre o protocolo
            try:
                linha = relocar_linha(pid)
                botao = linha.find_element(By.XPATH, ".//button[3]")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", botao
                )
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", botao)
                time.sleep(0.8)
            except (StaleElementReferenceException, TimeoutException):
                print("⚠ Não conseguiu abrir o protocolo — pulando")
                continue

            # Clica em Rejeitar
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(.,'Rejeitar')]")
                    )
                )
                clicar("//button[contains(.,'Rejeitar')]")
            except TimeoutException:
                print("⚠ Protocolo sem botão Rejeitar — pulando")
                clicar("//button[contains(.,'Cancelar')]")
                continue

            # Lê o motivo de rejeição
            try:
                campo = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//*[normalize-space()='Motivo Rejeição']/following::textarea[1]")
                    )
                )
                wait.until(
                    lambda d: campo.get_attribute("value").strip() != ""
                )
                motivo = campo.get_attribute("value").strip()
            except TimeoutException:
                print("⚠ Campo motivo não encontrado — pulando")
                clicar("//button[contains(.,'Cancelar')]")
                continue

            # Salva no arquivo
            with open(ARQUIVO_SAIDA, "a", encoding="utf-8") as f:
                f.write(
                    f"Protocolo: {pid}\n"
                    f"Seção: {secao}\n"
                    f"Data: {data_protocolo}\n"
                    f"Motivo:\n{motivo}\n"
                    f"{'-'*60}\n"
                )

            contador_total += 1
            print("📄 Motivo extraído")

            # Volta para a lista
            clicar("//button[contains(.,'Cancelar')]")
            clicar("//a[contains(.,'Documentos')]")
            clicar("//button[contains(.,'Consultar')]")
            esperar_tabela_estavel()
            ir_para_pagina(pagina_atual)

        # Avança para próxima página
        if ir_para_proxima_pagina(pagina_atual):
            pagina_atual += 1
        else:
            print("\n🏁 Última página alcançada")
            break

except KeyboardInterrupt:
    print("\n🛑 Interrompido pelo usuário")

finally:
    resumo = (
        "\n\n"
        "================ RESUMO FINAL ================\n"
        f"Motivos extraídos: {contador_total}\n"
        f"Protocolos únicos: {len(protocolos_unicos)}\n"
        f"Última página: {pagina_atual}\n"
        "==============================================\n"
    )

    print("\n📊 RESUMO FINAL")
    print(f"📄 Motivos extraídos: {contador_total}")
    print(f"📑 Protocolos únicos: {len(protocolos_unicos)}")
    print(f"📘 Última página: {pagina_atual}")
    print(f"💾 Arquivo: {ARQUIVO_SAIDA}")

    with open(ARQUIVO_SAIDA, "a", encoding="utf-8") as f:
        f.write(resumo)

    driver.quit()