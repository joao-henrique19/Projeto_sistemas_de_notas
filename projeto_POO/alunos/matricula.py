from datetime import datetime
from random import randint

CODIGOS_CURSO = {
    "Informática": "101",
    "Robótica": "202",
    "Eletrônica": "303",
    "Administração": "404",
    "Serviços Jurídicos": "505",
}


def gerar_matricula(curso, matriculas_cadastradas):
    """ANO + código do curso + 5 dígitos aleatórios (sem repetir)."""
    if curso not in CODIGOS_CURSO:
        raise ValueError("Curso inválido para gerar matrícula: " + str(curso))

    prefixo = str(datetime.now().year) + CODIGOS_CURSO[curso]
    while True:
        matricula = prefixo + str(randint(0, 99999)).zfill(5)
        if matricula not in matriculas_cadastradas:
            return matricula
