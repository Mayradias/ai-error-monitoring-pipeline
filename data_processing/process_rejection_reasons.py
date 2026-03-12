import pandas as pd
import re
from rapidfuzz import fuzz
import os

# ==========================================
# CONFIGURAÇÃO DE CAMINHO
# ==========================================

base_dir = os.path.dirname(os.path.abspath(__file__))

nome_txt = "motivos_rejeicao02MAR-06MAR.txt"

caminho_arquivo = os.path.join(base_dir, nome_txt)

nome_excel = nome_txt.replace(".txt", ".xlsx")
caminho_excel = os.path.join(base_dir, nome_excel)

# ==========================================
# LISTAS PARA ARMAZENAR DADOS
# ==========================================

protocolos = []
motivos = []

# ==========================================
# LEITURA DO ARQUIVO TXT
# ==========================================

with open(caminho_arquivo, "r", encoding="utf-8") as file:
    linhas = file.readlines()

for i in range(len(linhas)):
    
    linha = linhas[i].strip()

    if linha.startswith("Protocolo"):

        match = re.search(r"Protocolo\s+([\d\/\.\-]+)", linha)

        if match:

            protocolo = match.group(1)

            if i + 1 < len(linhas):

                motivo = linhas[i + 1].strip()

                protocolos.append(protocolo)
                motivos.append(motivo)

# ==========================================
# CRIAR DATAFRAME
# ==========================================

df = pd.DataFrame({
    "Protocolo": protocolos,
    "Motivo_Original": motivos
})

# ==========================================
# FUNÇÃO FUZZY
# ==========================================

def palavra_parecida(texto, palavra, limite=80):

    palavras_texto = texto.split()

    for p in palavras_texto:

        if fuzz.ratio(p, palavra) >= limite:
            return True

    return False

# ==========================================
# REGRAS DE CLASSIFICAÇÃO
# ==========================================

regras_simples = {
    "Erro de extração no cabeçalho": ["cabeçalho", "cabecalho", "nire"],
    "Erro de extração no preâmbulo": ["preambulo"],
    "Erro de espaçamento": ["espaçamento", "junto", "juntas"],
    "Erro de extração nos assinantes": ["assinante", "assinantes", "procurador", "representante", "testemunha"],
    "Alucinação nos assinantes": ["data", "local"],
    "Erro de extração no feixos": ["feixos"],
    "Erro de extração em nomes": ["um", "dois"],
    "Erro de extração no objeto social": ["objeto", "social"],
    "Erro de extração no logradouro": ["logradouro", "endereço"],
    "Erro de extração no RG": ["rg"],
    "Erro de extração no bairro": ["bairro"],
    "Erro de extração na filial": ["filial"],
    "Erro na extração de administradores": ["administrador", "administradora"],
    "Erro na alteração de capital": ["alteracao", "capital"],
    "Erro na distribuição de quotas": ["distribuicao", "quotas"],
    "Erro na extração do orgão expedidor": ["orgao", "expedidor"],
    "Erro de extração de palavras": ["sem", "ao", "invés"]
}

regras_compostas = [

    {
        "categoria": "Erro de extração no número e complemento",
        "condicoes": [["numero", "complemento"]]
    },

    {
        "categoria": "Erro na extração de entrada/saída de sócios",
        "condicoes": [
            ["entrada", "socio"],
            ["saida", "socio"]
        ]
    },

    {
        "categoria": "Erro na extração no preâmbulo da empresa",
        "condicoes": [
            ["informacoes", "empresa"],
            ["nome", "empresa"]
        ]
    }
]
# ==========================================
# FUNÇÃO DE CLASSIFICAÇÃO
# ==========================================

def classificar_motivo(texto):

    texto = texto.lower()

    categorias = []

    # Regras simples
    for categoria, palavras in regras_simples.items():

        for palavra in palavras:

            if palavra_parecida(texto, palavra):

                categorias.append(categoria)
                break

    # Regras compostas
    for regra in regras_compostas:

     for combinacao in regra["condicoes"]:

        if all(palavra_parecida(texto, p) for p in combinacao):

            categorias.append(regra["categoria"])
            break

    # Caso não encontre nada
    if not categorias:
        categorias.append("Outros")

    return categorias

# ==========================================
# APLICAR CLASSIFICAÇÃO
# ==========================================

df["Categoria"] = df["Motivo_Original"].apply(classificar_motivo)

# EXPLODIR PARA MULTIPLOS ERROS
df = df.explode("Categoria")

# ==========================================
# CLASSIFICAR TIPO DE ERRO
# ==========================================

def classificar_tipo_erro(categoria):

    categoria = categoria.lower()

    if "extração" in categoria:
        return "Erro de extração"

    elif "espaçamento" in categoria:
        return "Erro de extração"

    elif "distribuição" in categoria:
        return "Erro de extração"

    elif "alteração" in categoria:
        return "Erro de extração"

    elif "alucinação" in categoria:
        return "Erro de alucinação"

    elif "alocação" in categoria:
        return "Erro de regra"

    else:
        return "null"

df["Tipo de erro"] = df["Categoria"].apply(classificar_tipo_erro)

# ==========================================
# EXPORTAR EXCEL
# ==========================================

df.to_excel(caminho_excel, index=False, engine="openpyxl")

print(f"Arquivo Excel gerado com sucesso: {nome_excel}")