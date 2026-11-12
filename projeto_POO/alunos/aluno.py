from formatacoes.formatar_dados import (
    formatar_nome, formatar_cpf, formatar_telefone, formatar_cep
)


class Aluno:
    def __init__(self, nacionalidade, nome, data_nascimento, cpf, telefone,
                 cep, rua, numero, bairro, cidade, curso, serie,
                 matricula, email):
        self.nacionalidade = nacionalidade.strip().title()
        self.nome = formatar_nome(nome)
        self.data_nascimento = data_nascimento.strip()
        self.cpf = formatar_cpf(cpf)
        self.telefone = formatar_telefone(telefone)
        self.cep = formatar_cep(cep)
        self.rua = rua.strip().title()
        self.numero = numero.strip().upper()
        self.bairro = bairro.strip().title()
        self.cidade = cidade.strip().title()
        self.curso = curso
        self.serie = serie
        self.matricula = matricula
        self.email = email

    def dados_formatados(self):
        """Lista de (rótulo, valor) pronta para exibir em tela ou terminal."""
        return [
            ("Nome", self.nome),
            ("Matrícula", self.matricula),
            ("E-mail", self.email),
            ("Nacionalidade", self.nacionalidade),
            ("Data de nascimento", self.data_nascimento),
            ("CPF", self.cpf),
            ("Telefone", self.telefone),
            ("CEP", self.cep),
            ("Rua", self.rua),
            ("Número", self.numero),
            ("Bairro", self.bairro),
            ("Cidade", self.cidade),
            ("Curso", self.curso),
            ("Série", self.serie),
        ]

    def exibir_dados(self):
        print("\n--- DADOS DO ALUNO ---")
        for rotulo, valor in self.dados_formatados():
            print(rotulo + ":", valor)

    def to_dict(self):
        return dict(vars(self))

    @classmethod
    def from_dict(cls, dados):
        return cls(**dados)
