from datetime import date

MOTIVOS = [
    "Atestado médico",
    "Consulta ou exame",
    "Falecimento de familiar",
    "Convocação judicial ou militar",
    "Compromisso religioso",
    "Problema de transporte",
    "Outro",
]

STATUS_PENDENTE = "Pendente"
STATUS_DEFERIDA = "Deferida"
STATUS_INDEFERIDA = "Indeferida"
STATUS = (STATUS_PENDENTE, STATUS_DEFERIDA, STATUS_INDEFERIDA)

EXTENSOES_PERMITIDAS = (".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx")
TAMANHO_MAXIMO = 5 * 1024 * 1024  # 5 MB


def hoje_formatado():
    return date.today().strftime("%d/%m/%Y")


class Justificativa:
    """Pedido de justificativa de falta de um aluno em uma matéria.

    Enquanto está Pendente ou Indeferida, as horas continuam contando como
    falta. Quando é Deferida, as horas são abonadas no cálculo da frequência.
    """

    def __init__(self, id, aluno, materia, data_falta, horas, motivo,
                 descricao="", arquivo="", arquivo_original="",
                 status=STATUS_PENDENTE, parecer="", data_envio=None,
                 data_analise=""):
        self.id = id
        self.aluno = aluno
        self.materia = materia
        self.data_falta = data_falta
        self.horas = horas
        self.motivo = motivo
        self.descricao = descricao
        self.arquivo = arquivo                    # nome guardado na pasta de documentos
        self.arquivo_original = arquivo_original  # nome que o usuário escolheu
        self.status = status
        self.parecer = parecer
        self.data_envio = data_envio or hoje_formatado()
        self.data_analise = data_analise

    @property
    def tem_documento(self):
        return bool(self.arquivo)

    @property
    def deferida(self):
        return self.status == STATUS_DEFERIDA

    def exibir_dados(self):
        print("\n--- JUSTIFICATIVA DE FALTA ---")
        print("Aluno:", self.aluno.nome)
        print("Matéria:", self.materia.nome)
        print("Data da falta:", self.data_falta)
        print("Horas:", self.horas)
        print("Motivo:", self.motivo)
        print("Documento:", self.arquivo_original or "nenhum")
        print("Situação:", self.status)

    def to_dict(self):
        return {
            "id": self.id,
            "aluno": self.aluno.matricula,
            "materia": self.materia.id,
            "data_falta": self.data_falta,
            "horas": self.horas,
            "motivo": self.motivo,
            "descricao": self.descricao,
            "arquivo": self.arquivo,
            "arquivo_original": self.arquivo_original,
            "status": self.status,
            "parecer": self.parecer,
            "data_envio": self.data_envio,
            "data_analise": self.data_analise,
        }

    @classmethod
    def from_dict(cls, dados, aluno, materia):
        return cls(
            dados["id"], aluno, materia, dados["data_falta"], dados["horas"],
            dados["motivo"], dados.get("descricao", ""),
            dados.get("arquivo", ""), dados.get("arquivo_original", ""),
            dados.get("status", STATUS_PENDENTE), dados.get("parecer", ""),
            dados.get("data_envio"), dados.get("data_analise", ""),
        )
