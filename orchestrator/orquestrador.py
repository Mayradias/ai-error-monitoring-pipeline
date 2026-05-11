# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time

# ============================================================
# ORQUESTRADOR — AI ERROR MONITORING PIPELINE
#
# Sequência:
# 1. Automação de aprovados (manual: login + filtro + ENTER)
# 2. Automação de rejeitados (manual: login + filtro + ENTER)
# 3. Pipeline banco (automático)
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_APROVADOS  = os.path.join(BASE_DIR, "automationAPROVADOS.py")
SCRIPT_REJEITADOS = os.path.join(BASE_DIR, "automationcollect_rejection_reasons_ATUAL.py")
SCRIPT_PIPELINE   = os.path.join(BASE_DIR, "pipeline_banco.py")

PYTHON = sys.executable

def separador():
    print("\n" + "=" * 55)

def rodar_script(caminho, nome):
    separador()
    print(f"  INICIANDO: {nome}")
    separador()
    resultado = subprocess.run([PYTHON, caminho])
    if resultado.returncode != 0:
        print(f"\n❌ ERRO em '{nome}'. Verifique o log acima.")
        return False
    print(f"\n✅ '{nome}' concluído com sucesso.")
    return True

# ============================================================
# INÍCIO
# ============================================================

separador()
print("  AI ERROR MONITORING — ORQUESTRADOR")
separador()
print("""
Sequência de execução:
  1. Automação APROVADOS   (requer ação manual)
  2. Automação REJEITADOS  (requer ação manual)
  3. Pipeline BANCO        (automático)
""")
input("👉 Pressione ENTER para iniciar...")

# ============================================================
# ETAPA 1 — APROVADOS
# ============================================================

separador()
print("""
  ETAPA 1 DE 3 — APROVADOS

  O navegador vai abrir.
  Você deve:
    1. Fazer LOGIN
    2. Ir em DOCUMENTOS
    3. Filtrar por APROVADOS
    4. Clicar em CONSULTAR
    5. Pressionar ENTER no terminal quando a lista estiver visível
""")
input("👉 Pressione ENTER para abrir o navegador...")

ok = rodar_script(SCRIPT_APROVADOS, "automationAPROVADOS.py")
if not ok:
    print("\n⚠ Deseja continuar mesmo assim? (s/n)")
    resposta = input("→ ").strip().lower()
    if resposta != "s":
        print("Execução encerrada.")
        sys.exit(1)

# ============================================================
# ETAPA 2 — REJEITADOS
# ============================================================

separador()
print("""
  ETAPA 2 DE 3 — REJEITADOS

  O navegador vai abrir novamente.
  Você deve:
    1. Fazer LOGIN
    2. Ir em DOCUMENTOS
    3. Filtrar por REJEITADOS
    4. Clicar em CONSULTAR
    5. Pressionar ENTER no terminal quando a lista estiver visível
""")
input("👉 Pressione ENTER para abrir o navegador...")

ok = rodar_script(SCRIPT_REJEITADOS, "automationcollect_rejection_reasons_ATUAL.py")
if not ok:
    print("\n⚠ Deseja continuar mesmo assim? (s/n)")
    resposta = input("→ ").strip().lower()
    if resposta != "s":
        print("Execução encerrada.")
        sys.exit(1)

# ============================================================
# ETAPA 3 — PIPELINE BANCO
# ============================================================

separador()
print("""
  ETAPA 3 DE 3 — PIPELINE BANCO

  Processando e inserindo dados no PostgreSQL...
  Nenhuma ação necessária.
""")
time.sleep(2)

ok = rodar_script(SCRIPT_PIPELINE, "pipeline_banco.py")

# ============================================================
# CONCLUSÃO
# ============================================================

separador()
if ok:
    print("""
  ✅ PIPELINE CONCLUÍDO COM SUCESSO

  Os dados foram inseridos no banco de dados.
  O dashboard já reflete as informações atualizadas.
""")
else:
    print("""
  ⚠ PIPELINE CONCLUÍDO COM ERROS

  Verifique os logs acima para identificar o problema.
""")

separador()
input("👉 Pressione ENTER para encerrar...")
