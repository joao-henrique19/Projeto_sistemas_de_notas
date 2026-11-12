class Materia:
    def __init__(self, id, nome, professor, carga_horaria):
        self.id = id
        self.nome = nome
        self.professor = professor
        self.carga_horaria = carga_horaria

    def exibir_dados(self):
        print("\n--- DADOS DA MATÉRIA ---")
        print("Código:", self.id)
        print("Matéria:", self.nome)
        print("Professor:", self.professor.nome)
        print("Carga horária:", self.carga_horaria, "horas")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "professor": self.professor.matricula,
            "carga_horaria": self.carga_horaria,
        }

    @classmethod
    def from_dict(cls, dados, professor):
        return cls(dados["id"], dados["nome"], professor, dados["carga_horaria"])
