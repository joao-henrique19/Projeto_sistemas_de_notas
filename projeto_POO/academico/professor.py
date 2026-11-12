class Professor:
    def __init__(self, nome, matricula):
        self.nome = nome
        self.matricula = matricula

    def exibir_dados(self):
        print("\n--- DADOS DO PROFESSOR ---")
        print("Nome:", self.nome)
        print("Matrícula:", self.matricula)

    def to_dict(self):
        return {"nome": self.nome, "matricula": self.matricula}

    @classmethod
    def from_dict(cls, dados):
        return cls(dados["nome"], dados["matricula"])
