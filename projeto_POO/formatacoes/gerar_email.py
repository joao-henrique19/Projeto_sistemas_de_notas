import unicodedata


def remover_acentos(texto):
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def gerar_email(nome, emails_cadastrados):
    """Gera 'primeiro.ultimo@aluno.escola.com' sem acentos e sem repetir e-mails."""
    partes = []
    for parte in remover_acentos(nome).lower().split():
        parte = "".join(c for c in parte if c.isalnum())
        if parte:
            partes.append(parte)

    if len(partes) == 0:
        base = "aluno"
    elif len(partes) == 1:
        base = partes[0]
    else:
        base = partes[0] + "." + partes[-1]

    dominio = "@aluno.escola.com"
    email = base + dominio
    contador = 1
    while email in emails_cadastrados:
        email = base + str(contador) + dominio
        contador += 1

    emails_cadastrados.append(email)
    return email
