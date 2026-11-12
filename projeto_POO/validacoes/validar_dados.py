import math
from datetime import date

CURSOS = ["Informática", "Robótica", "Eletrônica", "Administração", "Serviços Jurídicos"]
SERIES = ["6º Ano", "7º Ano", "8º Ano", "9º Ano", "1º Ano", "2º Ano", "3º Ano"]


def validar_nome(nome):
    """Aceita apenas letras, espaços, apóstrofo, hífen e ponto (mínimo 3 caracteres)."""
    nome = nome.strip()
    if len(nome) < 3:
        return False
    tem_letra = False
    for caractere in nome:
        if caractere.isalpha():
            tem_letra = True
        elif caractere not in " '-.":
            return False
    return tem_letra


def validar_cpf(cpf):
    cpf = cpf.replace(".", "").replace("-", "").replace(" ", "")
    if len(cpf) != 11 or not cpf.isdecimal():
        return False
    if cpf == cpf[0] * 11:
        return False

    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[9]):
        return False

    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[10]):
        return False
    return True


def validar_data(data):
    partes = data.strip().split("/")
    if len(partes) != 3:
        return False
    if not all(parte.isdecimal() for parte in partes):
        return False

    dia = int(partes[0])
    mes = int(partes[1])
    ano = int(partes[2])

    if ano < 1900 or mes < 1 or mes > 12:
        return False

    dias_do_mes = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if ano % 400 == 0 or (ano % 4 == 0 and ano % 100 != 0):
        dias_do_mes = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    if dia < 1 or dia > dias_do_mes[mes - 1]:
        return False
    return True


def validar_data_passada(data):
    """Data válida (DD/MM/AAAA) que não esteja no futuro."""
    if not validar_data(data):
        return False
    dia, mes, ano = (int(parte) for parte in data.strip().split("/"))
    hoje = date.today()
    if ano > hoje.year:
        return False
    return date(ano, mes, dia) <= hoje


def validar_data_nascimento(data):
    """Data válida e que não esteja no futuro."""
    return validar_data_passada(data)


def normalizar_curso(curso):
    """Devolve o nome oficial do curso (ou None se não existir)."""
    for nome_curso in CURSOS:
        if curso.strip().lower() == nome_curso.lower():
            return nome_curso
    return None


def normalizar_serie(serie):
    """Devolve o nome oficial da série (ou None se não existir)."""
    for nome_serie in SERIES:
        if serie.strip().lower() == nome_serie.lower():
            return nome_serie
    return None


def validar_curso(curso):
    return normalizar_curso(curso) is not None


def validar_serie(serie):
    return normalizar_serie(serie) is not None


def converter_nota(texto):
    """Converte '85', '72,5' ou '72.5' em float entre 0 e 100. Devolve None se inválida."""
    try:
        nota = float(str(texto).strip().replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(nota) or nota < 0 or nota > 100:
        return None
    return nota
