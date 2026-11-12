MEDIA_MINIMA = 60        # média mínima (escala de 0 a 100)
FREQUENCIA_MINIMA = 75   # frequência mínima em %


def formatar_nota(nota):
    return format(nota, "g")


class Boletim:
    def __init__(self, aluno, materia, notas, faltas, faltas_justificadas=0):
        self.aluno = aluno
        self.materia = materia
        self.notas = list(notas)
        self.faltas = faltas
        # horas de faltas com justificativa deferida (a Escola mantém atualizado)
        self.faltas_justificadas = faltas_justificadas
        self.media = sum(self.notas) / len(self.notas)

    @property
    def faltas_efetivas(self):
        """Faltas que realmente contam para a frequência."""
        return max(0, self.faltas - self.faltas_justificadas)

    @property
    def faltas_abonadas(self):
        """Quantas horas de falta foram abonadas por justificativas deferidas."""
        return self.faltas - self.faltas_efetivas

    @property
    def frequencia(self):
        carga = self.materia.carga_horaria
        return ((carga - self.faltas_efetivas) / carga) * 100

    @property
    def situacao(self):
        motivos = []
        if self.media < MEDIA_MINIMA:
            motivos.append("nota")
        if self.frequencia < FREQUENCIA_MINIMA:
            motivos.append("falta")
        if not motivos:
            return "Aprovado"
        return "Reprovado por " + " e ".join(motivos)

    @property
    def aprovado(self):
        return self.situacao == "Aprovado"

    def notas_formatadas(self):
        return " / ".join(formatar_nota(n) for n in self.notas)

    def exibir_dados(self):
        print("\n--- BOLETIM ---")
        print("Aluno:", self.aluno.nome)
        print("Matéria:", self.materia.nome)
        print("Notas:", self.notas_formatadas())
        print("Média:", round(self.media, 2))
        print("Faltas:", self.faltas, "(abonadas:", str(self.faltas_abonadas) + ")")
        print("Frequência:", round(self.frequencia, 2), "%")
        print("Situação:", self.situacao)

    def to_dict(self):
        return {
            "aluno": self.aluno.matricula,
            "materia": self.materia.id,
            "notas": self.notas,
            "faltas": self.faltas,
        }

    @classmethod
    def from_dict(cls, dados, aluno, materia):
        return cls(aluno, materia, dados["notas"], dados["faltas"])
