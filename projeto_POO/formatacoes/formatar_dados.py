PARTICULAS = {"da", "de", "do", "das", "dos", "e"}


def formatar_nome(nome):
    """'maria DA silva' -> 'Maria da Silva'."""
    palavras = nome.strip().lower().split()
    resultado = []
    for posicao, palavra in enumerate(palavras):
        if posicao > 0 and palavra in PARTICULAS:
            resultado.append(palavra)
        else:
            resultado.append(palavra.capitalize())
    return " ".join(resultado)


def formatar_cpf(cpf):
    cpf = cpf.strip().replace(".", "").replace("-", "").replace(" ", "")
    if len(cpf) != 11 or not cpf.isdigit():
        return None
    return cpf[0:3] + "." + cpf[3:6] + "." + cpf[6:9] + "-" + cpf[9:11]


def formatar_telefone(telefone):
    telefone = telefone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
    if not telefone.isdigit():
        return None
    if len(telefone) == 11:
        return "(" + telefone[0:2] + ") " + telefone[2] + " " + telefone[3:7] + "-" + telefone[7:11]
    if len(telefone) == 10:
        return "(" + telefone[0:2] + ") " + telefone[2:6] + "-" + telefone[6:10]
    return None


def formatar_cep(cep):
    cep = cep.strip().replace("-", "").replace(" ", "")
    if len(cep) != 8 or not cep.isdigit():
        return None
    return cep[0:5] + "-" + cep[5:8]
