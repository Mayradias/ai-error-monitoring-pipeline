# -*- coding: utf-8 -*-
import pandas as pd
import re
import os
import psycopg2
from rapidfuzz import fuzz

# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# Altere apenas as informações abaixo
# ============================================================

DB_HOST     = "127.0.0.1"
DB_PORT     = 0000
DB_NAME     = "ai_error_monitoring"
DB_USER     = "postgres"
DB_PASSWORD = "sua_senha_aqui"  

# ============================================================
# CONFIGURAÇÃO DE CAMINHOS
# Aponte para os arquivos .txt gerados pelas automações
# ============================================================

base_dir = os.path.dirname(os.path.abspath(__file__))

nome_txt_rejeitados = "motivos_rejeicao.txt"
nome_txt_aprovados  = "protocolos_aprovados.txt"

caminho_rejeitados = os.path.join(base_dir, nome_txt_rejeitados)
caminho_aprovados  = os.path.join(base_dir, nome_txt_aprovados)

# ============================================================
# FUNÇÃO: PALAVRA PARECIDA (FUZZY)
# Compara token por token com tolerância a erros de digitação
# ============================================================

def palavra_parecida(texto, palavra, limite=80):
    palavras_texto = texto.split()
    for p in palavras_texto:
        if fuzz.ratio(p, palavra) >= limite:
            return True
    return False

# ============================================================
# REGRAS DE ALUCINAÇÃO
# Ativadas apenas quando "alucinação/alucinou" é detectado
# Subcategorias separadas por contexto
# ============================================================

regras_alucinacao = {
    "Alucinação na data e/ou local de assinatura": {
        "simples": ["data", "local"],
        "compostas": [["data", "assinatura"], ["local", "assinatura"],
                      ["data", "assinantes"], ["local", "assinantes"]]
    },
    "Alucinação no nome da empresa": {
        "simples": [],
        "compostas": [["nome", "empresa"]]
    },
    "Alucinação no nome do sócio": {
        "simples": [],
        "compostas": [["nome", "sócio"], ["nome", "sócia"]]
    },
    "Alucinação no endereço": {
        "simples": ["foro", "logradouro"],
        "compostas": [["tipo", "logradouro"]]
    },
    "Alucinação no representante legal": {
        "simples": ["representante", "procurador"],
        "compostas": []
    },
    "Alucinação no capital social": {
        "simples": [],
        "compostas": [["capital", "social"]]
    },
    "Alucinação nos assinantes": {
        "simples": ["assinantes", "assinante"],
        "compostas": []
    },
}

# ============================================================
# REGRAS COMPOSTAS DE EXTRAÇÃO
# Verificadas ANTES das simples — combinação de palavras-chave
# Ao encontrar match, retorna imediatamente
# ============================================================

regras_compostas_extracao = [
    # SÓCIO
    {"categoria": "Erro de extração nos dados de sócios",
     "condicoes": [["nome", "sócio"], ["nome", "sócia"],
                   ["dados", "sócio"], ["sobrenome", "sócio"]]},

    # ENTRADA/SAÍDA DE SÓCIOS
    {"categoria": "Erro na extração de entrada/saída de sócios",
     "condicoes": [["entrada", "sócio"], ["saída", "sócio"],
                   ["entrada", "socio"], ["saida", "socio"], ["sócio", "ingressante"]]},

    # NOME DA EMPRESA
    {"categoria": "Erro de extração no nome da empresa",
     "condicoes": [["nome", "empresa"]]},

    # PREÂMBULO DA EMPRESA
    {"categoria": "Erro de extração no preâmbulo",
     "condicoes": [["dados", "empresa"], ["informações", "empresa"],
                   ["informacoes", "empresa"]]},

    # ASSINANTES
    {"categoria": "Erro de extração nos assinantes",
     "condicoes": [["nome", "assinante"], ["assinatura", "assinante"],
                   ["data", "assinante"], ["local", "assinante"]]},

    # ADMINISTRADOR
    {"categoria": "Erro na extração de administradores",
     "condicoes": [["administrador", "sócio"], ["administradora", "sócia"],
                   ["sócio", "administrador"], ["sócia", "administradora"]]},

    # ENDEREÇO COMPOSTO
    {"categoria": "Erro de extração no endereço",
     "condicoes": [["número", "endereço"], ["numero", "endereco"],
                   ["uf", "endereço"], ["tipo", "logradouro"],
                   ["município", "complemento"], ["municipio", "complemento"]]},
    
    # CAPITAL SOCIAL 
    {"categoria": "Erro na extração do capital social",
     "condicoes": [["capital", "social"]]},

    # NOME FANTASIA 
    {"categoria": "Erro de extração no nome fantasia", 
     "condicoes": [["nome", "fantasia"]]},

    # REPRESENTANTE
    {"categoria": "Erro de extração nos representantes",
     "condicoes": [["nome", "representante"], ["representante"]]},

    # OBJETO SOCIAL + ESPAÇAMENTO
    {"categoria": "Erro de extração no objeto social",
     "condicoes": [["junto", "objeto"], ["juntos", "objeto"], 
                   ["juntas", "objeto"], ["objeto", "social"], ["espacamento", "indevido"]]},

    # CLÁUSULAS
    {"categoria": "Erro de extração em cláusulas",
     "condicoes": [["seção", "cláusula"], ["secao", "clausula"]]},
]

# ============================================================
# REGRAS SIMPLES DE EXTRAÇÃO
# Verificadas após as compostas
# Palavra isolada já classifica — ordem define prioridade
# Ao encontrar match, retorna imediatamente
# ============================================================

regras_simples_extracao = [
    ("Erro de extração no cabeçalho",           ["cabeçalho", "cabecalho", "nire", "cnpj"]),
    ("Erro de extração no preâmbulo",            ["preâmbulo", "preambulo"]),
    ("Erro de extração no feixos",               ["feixos"]),
    ("Erro de extração em consolidação",         ["consolidação", "consolidacao"]),
    ("Erro de extração em cláusulas",            ["cláusula", "clausula", "transformação", "duração"]),
    ("Erro de extração no enquadramento",        ["enquadramento"]),
    ("Erro de extração no endereço",             ["logradouro", "bairro", "cep", "complemento",
                                                   "município", "municipio", "endereço", "numero", "endereco"]),
    ("Erro de extração nos assinantes",          ["assinante", "assinantes", "testemunha"]),
    ("Erro de extração no RG",                   ["rg"]),
    ("Erro de extração na filial",               ["filial"]),
    ("Erro na extração do órgão expedidor",      ["expedidor"]),
    ("Erro na extração de administradores",      ["administrador", "administradora"]),
    ("Erro na alteração de capital e quotas",    ["quotas", "capital"]),
    ("Erro de extração na natureza jurídica",    ["natureza"]),
    ("Erro de espaçamento ou junção de palavras", ["espaçamento", "junto", "juntas", "juntos"]),
    ("Erro de extração de caracteres ou letras", ["caracter", "caractere", "letra", "letras"]),
]

# ============================================================
# FUNÇÃO: CLASSIFICAR ALUCINAÇÃO
# ============================================================

def classificar_alucinacao(texto):
    """
    Tenta encaixar em uma subcategoria de alucinação.
    Verifica compostas primeiro, depois simples.
    Retorna a primeira categoria encontrada.
    """
    for categoria, regras in regras_alucinacao.items():
        # Compostas
        for combinacao in regras["compostas"]:
            if all(palavra_parecida(texto, p) for p in combinacao):
                return categoria
        # Simples
        for palavra in regras["simples"]:
            if palavra_parecida(texto, palavra):
                return categoria

    return "Alucinação - Outros"

# ============================================================
# FUNÇÃO: CLASSIFICAR MOTIVO
#
# Prioridade:
# 1. Detecta "alucinação/alucinou" → regras de alucinação → retorna
# 2. Regras compostas de extração → ao encontrar match → retorna
# 3. Regras simples de extração → ao encontrar match → retorna
# 4. "Outros" se nada encontrar
# ============================================================

def classificar_motivo(texto):
    texto_lower = texto.lower()

    # ========================
    # PASSO 1: ALUCINAÇÃO
    # ========================
    eh_alucinacao = any([
        palavra_parecida(texto_lower, "alucinação"),
        palavra_parecida(texto_lower, "alucinacao"),
        palavra_parecida(texto_lower, "alucinou")
    ])

    if eh_alucinacao:
        return [classificar_alucinacao(texto_lower)]

    # ========================
    # PASSO 2: COMPOSTAS
    # ========================
    for regra in regras_compostas_extracao:
        for combinacao in regra["condicoes"]:
            if all(palavra_parecida(texto_lower, p) for p in combinacao):
                return [regra["categoria"]]

    # ========================
    # PASSO 3: SIMPLES
    # ========================
    for categoria, palavras in regras_simples_extracao:
        for palavra in palavras:
            if palavra_parecida(texto_lower, palavra):
                return [categoria]

    # ========================
    # PASSO 4: OUTROS
    # ========================
    return ["Outros"]


def classificar_tipo_erro(categoria):
    cat = categoria.lower()
    if "alucinação" in cat:
        return "Erro de alucinação"
    elif "outros" in cat:
        return "Não classificado"
    else:
        return "Erro de extração"

# ============================================================
# FUNÇÃO: CRIAR TABELA SE NÃO EXISTIR
# ============================================================

def criar_tabela(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS protocolos (
            id                SERIAL PRIMARY KEY,
            numero_protocolo  TEXT        NOT NULL,
            secao             TEXT,
            status            TEXT        NOT NULL,
            data_protocolo    TIMESTAMP,
            motivo_rejeicao   TEXT        DEFAULT 'N/A',
            categoria         TEXT        DEFAULT 'N/A',
            tipo_erro         TEXT        DEFAULT 'N/A',
            inserido_em       TIMESTAMP   DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS execucoes_pipeline (
            id                          SERIAL PRIMARY KEY,
            executado_em                TIMESTAMP DEFAULT NOW(),
            total_aprovados             INTEGER DEFAULT 0,
            total_rejeitados            INTEGER DEFAULT 0,
            total_erros_classificados   INTEGER DEFAULT 0,
            status_execucao             TEXT,
            observacao                  TEXT
        );
    """)

# ============================================================
# FUNÇÃO: LER TXT DE REJEITADOS
# ============================================================

def ler_rejeitados(caminho):
    registros = []

    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()

        if "Protocolo:" in linha:
            match = re.search(r"Protocolo:\s*([^\s]+)", linha)
            if match:
                protocolo = match.group(1)
                secao = data = motivo = None

                j = i + 1
                while j < len(linhas):
                    l = linhas[j].strip()
                    l_norm = l.replace("Seção:", "Secao:")

                    if "Secao:" in l_norm:
                        secao = l_norm.split("Secao:")[-1].strip()
                    elif "Data:" in l:
                        data = l.split("Data:")[-1].strip()
                    elif "Motivo:" in l:
                        if j + 1 < len(linhas):
                            motivo = linhas[j + 1].strip()
                        break
                    elif "Protocolo:" in l and j != i:
                        break
                    j += 1

                if motivo:
                    registros.append({
                        "Protocolo":       protocolo,
                        "Data":            data.strip() if data else None,
                        "Seção":           secao if secao else "N/A",
                        "Motivo_Rejeição": motivo
                    })
        i += 1

    df = pd.DataFrame(registros)
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y %H:%M", errors="coerce")
    return df

# ============================================================
# FUNÇÃO: LER TXT DE APROVADOS
# ============================================================

def ler_aprovados(caminho):
    registros = []

    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    for linha in linhas:
        linha = linha.strip()
        if not linha.startswith("Protocolo:"):
            continue

        partes = linha.split("|")
        protocolo = secao = data = None

        for p in partes:
            p = p.strip()
            if p.startswith("Protocolo:"):
                protocolo = p.replace("Protocolo:", "").strip()
            elif p.startswith("Seção:"):
                secao = p.replace("Seção:", "").strip()
            elif p.startswith("Data:"):
                data = p.replace("Data:", "").strip()

        if protocolo:
            registros.append({
                "Protocolo": protocolo,
                "Seção":     secao if secao else "N/A",
                "Data":      data
            })

    df = pd.DataFrame(registros)
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y %H:%M", errors="coerce")
    return df

# ============================================================
# FUNÇÃO: INSERIR NO BANCO
# ============================================================

def inserir_no_banco(df_rejeitados, df_aprovados):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD.encode('utf-8').decode('utf-8')
    )
    cur  = conn.cursor()

    total_aprovados           = 0
    total_rejeitados          = 0
    total_erros_classificados = 0

    try:
        criar_tabela(cur)

        # --------------------------------------------------
        # INSERIR APROVADOS
        # --------------------------------------------------
        print(f"\n📥 Inserindo aprovados...")

        for _, row in df_aprovados.iterrows():

            # Evita duplicatas: mesmo protocolo + seção + status
            cur.execute("""
                SELECT id FROM protocolos
                WHERE numero_protocolo = %s AND secao = %s AND status = 'APROVADO'
            """, (row["Protocolo"], row["Seção"]))

            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO protocolos
                        (numero_protocolo, secao, status, data_protocolo,
                         motivo_rejeicao, categoria, tipo_erro)
                    VALUES (%s, %s, 'APROVADO', %s, 'N/A', 'N/A', 'N/A')
                """, (row["Protocolo"], row["Seção"], row["Data"]))
                total_aprovados += 1

        # --------------------------------------------------
        # INSERIR REJEITADOS + CLASSIFICAÇÃO
        # --------------------------------------------------
        print(f"📥 Inserindo rejeitados e classificando erros...")

        for _, row in df_rejeitados.iterrows():
            categorias = classificar_motivo(row["Motivo_Rejeição"])

            for categoria in categorias:
                tipo = classificar_tipo_erro(categoria)

                # Evita duplicatas: mesmo protocolo + seção + categoria + data
                cur.execute("""
                    SELECT id FROM protocolos
                    WHERE numero_protocolo = %s AND secao = %s AND categoria = %s AND data_protocolo = %s
                """, (row["Protocolo"], row["Seção"], categoria, row["Data"]))

                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO protocolos
                            (numero_protocolo, secao, status, data_protocolo,
                             motivo_rejeicao, categoria, tipo_erro)
                        VALUES (%s, %s, 'REJEITADO', %s, %s, %s, %s)
                    """, (
                        row["Protocolo"],
                        row["Seção"],
                        row["Data"],
                        row["Motivo_Rejeição"],
                        categoria,
                        tipo
                    ))
                    total_rejeitados += 1
                    total_erros_classificados += 1

        # --------------------------------------------------
        # REGISTRAR EXECUÇÃO
        # --------------------------------------------------
        cur.execute("""
            INSERT INTO execucoes_pipeline
                (total_aprovados, total_rejeitados, total_erros_classificados,
                 status_execucao, observacao)
            VALUES (%s, %s, %s, 'SUCESSO', %s)
        """, (
            total_aprovados,
            total_rejeitados,
            total_erros_classificados,
            f"Rejeitados: {nome_txt_rejeitados} | Aprovados: {nome_txt_aprovados}"
        ))

        conn.commit()

        print(f"\n✅ INSERÇÃO CONCLUÍDA")
        print(f"   ✔ Aprovados inseridos:          {total_aprovados}")
        print(f"   ✔ Rejeitados inseridos:         {total_rejeitados}")
        print(f"   ✔ Erros classificados:          {total_erros_classificados}")

    except Exception as e:
        conn.rollback()

        try:
            cur.execute("""
                INSERT INTO execucoes_pipeline
                    (total_aprovados, total_rejeitados, total_erros_classificados,
                     status_execucao, observacao)
                VALUES (0, 0, 0, 'ERRO', %s)
            """, (str(e),))
            conn.commit()
        except:
            pass

        print(f"\n❌ ERRO durante a inserção: {e}")
        raise

    finally:
        cur.close()
        conn.close()

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  AI ERROR MONITORING — PIPELINE BANCO DE DADOS")
    print("=" * 55)

    # Lê rejeitados
    if os.path.exists(caminho_rejeitados):
        print(f"\n📄 Lendo rejeitados: {nome_txt_rejeitados}")
        df_rejeitados = ler_rejeitados(caminho_rejeitados)
        print(f"   {len(df_rejeitados)} blocos encontrados")
    else:
        print(f"\n⚠ Arquivo de rejeitados não encontrado: {caminho_rejeitados}")
        df_rejeitados = pd.DataFrame(
            columns=["Protocolo", "Data", "Seção", "Motivo_Rejeição"]
        )

    # Lê aprovados
    if os.path.exists(caminho_aprovados):
        print(f"📄 Lendo aprovados: {nome_txt_aprovados}")
        df_aprovados = ler_aprovados(caminho_aprovados)
        print(f"   {len(df_aprovados)} registros encontrados")
    else:
        print(f"\n⚠ Arquivo de aprovados não encontrado: {caminho_aprovados}")
        df_aprovados = pd.DataFrame(columns=["Protocolo", "Seção", "Data"])

    # Insere no banco
    inserir_no_banco(df_rejeitados, df_aprovados)