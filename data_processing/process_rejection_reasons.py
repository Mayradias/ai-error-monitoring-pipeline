import pandas as pd
import re
from rapidfuzz import fuzz
import os

# ==========================================
# CONFIGURAÇÃO DE CAMINHO
# ==========================================

# Pasta onde está o script
base_dir = os.path.dirname(os.path.abspath(__file__))

# ÚNICA COISA QUE VOCÊ ALTERA:
nome_txt = "motivo_rejeicao_exemplo.txt"

caminho_arquivo = os.path.join(base_dir, nome_txt)

# Gerar nome do Excel automaticamente
nome_excel = nome_txt.replace(".txt", ".xlsx")
caminho_excel = os.path.join(base_dir, nome_excel)

# ==========================================
# LISTAS PARA ARMAZENAR DADOS
# ==========================================

protocolos = []
motivos = []

# ==========================================
# LEITURA DO ARQUIVO
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
# FUNÇÃO AUXILIAR FUZZY
# ==========================================

def palavra_parecida(texto, palavra, limite=80):
    palavras_texto = texto.split()
    for p in palavras_texto:
        if fuzz.ratio(p, palavra) >= limite:
            return True
    return False

# ==========================================
# FUNÇÃO DE CLASSIFICAÇÃO
# ==========================================

def classificar_motivo(texto):
    texto = texto.lower()
    
    if palavra_parecida(texto, "nire"):
        if palavra_parecida(texto, "preambulo"):
            return "Erro de extração no preâmbulo"
        else:
            return "Erro de extração no cabeçalho"
    
    if palavra_parecida(texto, "cabeçalho") or palavra_parecida(texto, "cabecalho"):
        return "Erro de extração no cabeçalho"
    
    if palavra_parecida(texto, "cnpj"):
        if palavra_parecida(texto, "cabeçalho"):
            return "Erro de extração no cabeçalho"
        else:
            return "Erro de extração no preâmbulo"
    
    if (palavra_parecida(texto, "espaçamento") or 
        palavra_parecida(texto, "junto") or
        palavra_parecida(texto, "juntos") or
        palavra_parecida(texto, "juntas")):
        return "Erro de espaçamento"
    
    if (palavra_parecida(texto, "assinante") or 
        palavra_parecida(texto, "assinantes") or
        palavra_parecida(texto, "representante") or 
        palavra_parecida(texto, "testemunha")):
        return "Erro de extração nos assinantes"
    
    if (palavra_parecida(texto, "data") or 
        palavra_parecida(texto, "local")):
        return "Alucinação nos assinantes"
    
    if palavra_parecida(texto, "feixos"):
        return "Erro de extração no feixos"
    
    if ("um só" in texto or 
        "só um" in texto or 
        " dois " in texto):
        return "Erro de extração em nomes"
    
    if (palavra_parecida(texto, "objeto") or 
        palavra_parecida(texto, "social")):
        return "Erro de extração no objeto social"
    
    if palavra_parecida(texto, "preambulo"):
        return "Erro de extração no preâmbulo"
    
    if (palavra_parecida(texto, "logradouro") or 
        palavra_parecida(texto, "endereço")):
        return "Erro de extração no logradouro"
    
    if palavra_parecida(texto, "clausula"):
        return "Erro de extração em cláusulas"
    
    if (palavra_parecida(texto, "rg") or 
        palavra_parecida(texto, "RG")):
        return "Erro de extração no RG"
    
    if palavra_parecida(texto, "bairro"):
        return "Erro de extração no bairro"
    
    if (palavra_parecida(texto,"distribuicao") or 
        palavra_parecida(texto, "quotas")):
        return "Erro na distribuição de quotas"
    
    if (palavra_parecida(texto, "entrada") or 
        palavra_parecida(texto, "saida") or 
        palavra_parecida(texto, "entrando") or 
        palavra_parecida(texto, "saindo")):
        return "Erro na extração de entrada/saída de sócios"
    
    if (palavra_parecida(texto, "nome") or 
        palavra_parecida(texto, "errado") or 
        palavra_parecida(texto, "incorreto")):
        return "Erro na extração do nome de sócios/adm's"
    
    if (palavra_parecida(texto, "info") or 
        palavra_parecida(texto, "informacoes") or 
        palavra_parecida(texto, "empresa")):
        return "Erro na extração no preâmbulo da empresa"
    
    if (palavra_parecida(texto, "sem") or 
        palavra_parecida(texto, "ao") or 
        palavra_parecida(texto, "invés")):
        return "Erro de extração de palavras"

    return "Outros"

# Aplicar classificação
df["Categoria"] = df["Motivo_Original"].apply(classificar_motivo)

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
    elif "alucinação" in categoria:
        return "Erro de alucinação"
    else:
        return "null"

df["Tipo de erro"] = df["Categoria"].apply(classificar_tipo_erro)

# ==========================================
# EXPORTAR EXCEL
# ==========================================

df.to_excel(caminho_excel, index=False, engine="openpyxl")

print(f"Arquivo Excel gerado com sucesso: {nome_excel}") 
