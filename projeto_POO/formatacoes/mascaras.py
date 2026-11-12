"""Máscaras de digitação: recebem o texto digitado e devolvem o texto formatado."""


def _digitos(texto, limite):
    return "".join(c for c in texto if c.isdigit())[:limite]


def mascara_cpf(texto):
    d = _digitos(texto, 11)
    saida = d[0:3]
    if len(d) > 3:
        saida += "." + d[3:6]
    if len(d) > 6:
        saida += "." + d[6:9]
    if len(d) > 9:
        saida += "-" + d[9:11]
    return saida


def mascara_cep(texto):
    d = _digitos(texto, 8)
    if len(d) <= 5:
        return d
    return d[0:5] + "-" + d[5:8]


def mascara_data(texto):
    d = _digitos(texto, 8)
    saida = d[0:2]
    if len(d) > 2:
        saida += "/" + d[2:4]
    if len(d) > 4:
        saida += "/" + d[4:8]
    return saida


def mascara_telefone(texto):
    d = _digitos(texto, 11)
    if len(d) == 0:
        return ""
    if len(d) <= 2:
        return "(" + d
    ddd = "(" + d[0:2] + ") "
    if len(d) == 11:
        return ddd + d[2] + " " + d[3:7] + "-" + d[7:11]
    resto = d[2:]
    if len(resto) <= 4:
        return ddd + resto
    return ddd + resto[0:4] + "-" + resto[4:]
