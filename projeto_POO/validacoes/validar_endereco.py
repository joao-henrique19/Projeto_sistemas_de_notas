def validar_texto(valor):
    if valor.strip() == "":
        return False
    tem_letra = False
    for caractere in valor:
        if caractere.isalpha():
            tem_letra = True
    return tem_letra


def validar_numero(numero):
    if numero.isdigit():
        return True
    if numero.upper() == "S/N":
        return True
    return False
