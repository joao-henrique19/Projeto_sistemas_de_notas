def validar_telefone(telefone):
    telefone = telefone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if not telefone.isdigit():
        return False
    if len(telefone) != 10 and len(telefone) != 11:
        return False
    return True


def validar_cep(cep):
    cep = cep.replace("-", "").replace(" ", "")
    if len(cep) != 8 or not cep.isdigit():
        return False
    return True
