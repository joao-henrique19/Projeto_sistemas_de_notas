import os
import tempfile
import unittest

from escola import Escola, ErroCadastro

CPF_1 = "529.982.247-25"
CPF_2 = "111.444.777-35"


def dados_aluno(**extra):
    dados = dict(
        nacionalidade="brasileira", nome="joão da silva",
        data_nascimento="15/03/2008", cpf=CPF_1, telefone="83912345678",
        cep="58300000", rua="rua das flores", numero="123",
        bairro="centro", cidade="santa rita",
        curso="informática", serie="1º ano",
    )
    dados.update(extra)
    return dados


class TesteAlunos(unittest.TestCase):
    def setUp(self):
        self.escola = Escola()

    def test_cadastro_formata_e_gera_matricula_e_email(self):
        aluno = self.escola.cadastrar_aluno(**dados_aluno())
        self.assertEqual(aluno.nome, "João da Silva")
        self.assertEqual(aluno.cpf, CPF_1)
        self.assertEqual(aluno.telefone, "(83) 9 1234-5678")
        self.assertEqual(aluno.cep, "58300-000")
        self.assertEqual(aluno.curso, "Informática")
        self.assertEqual(aluno.serie, "1º Ano")
        self.assertEqual(aluno.email, "joao.silva@aluno.escola.com")
        self.assertEqual(len(aluno.matricula), 12)          # ano + curso + 5 dígitos
        self.assertEqual(aluno.matricula[4:7], "101")       # código de Informática

    def test_email_repetido_ganha_numero(self):
        a = self.escola.cadastrar_aluno(**dados_aluno())
        b = self.escola.cadastrar_aluno(**dados_aluno(cpf=CPF_2))
        self.assertEqual(a.email, "joao.silva@aluno.escola.com")
        self.assertEqual(b.email, "joao.silva1@aluno.escola.com")
        self.assertNotEqual(a.matricula, b.matricula)

    def test_nome_com_uma_palavra(self):
        aluno = self.escola.cadastrar_aluno(**dados_aluno(nome="Maria"))
        self.assertEqual(aluno.email, "maria@aluno.escola.com")

    def test_cpf_duplicado_e_invalido(self):
        self.escola.cadastrar_aluno(**dados_aluno())
        with self.assertRaises(ErroCadastro):
            self.escola.cadastrar_aluno(**dados_aluno())
        with self.assertRaises(ErroCadastro):
            self.escola.cadastrar_aluno(**dados_aluno(cpf="123.456.789-00"))

    def test_campos_invalidos(self):
        invalidos = [
            dict(nome="J1"), dict(nome="123abc"),
            dict(data_nascimento="31/02/2008"),
            dict(data_nascimento="01/01/2999"),
            dict(telefone="123"), dict(cep="123"), dict(numero="abc"),
            dict(rua="  "), dict(curso="Culinária"), dict(serie=""),
        ]
        for extra in invalidos:
            with self.subTest(extra=extra):
                with self.assertRaises(ErroCadastro):
                    self.escola.cadastrar_aluno(**dados_aluno(**extra))
        self.assertEqual(self.escola.alunos, [])

    def test_buscar(self):
        self.escola.cadastrar_aluno(**dados_aluno())
        self.escola.cadastrar_aluno(
            **dados_aluno(nome="Ana Souza", cpf=CPF_2, curso="Robótica")
        )
        self.assertEqual(len(self.escola.buscar_alunos("")), 2)
        self.assertEqual(len(self.escola.buscar_alunos("rob")), 1)
        self.assertEqual(len(self.escola.buscar_alunos("JOÃO")), 1)


class TesteAcademico(unittest.TestCase):
    def setUp(self):
        self.escola = Escola()
        self.aluno = self.escola.cadastrar_aluno(**dados_aluno())
        self.prof = self.escola.cadastrar_professor("carlos de lima")
        self.materia = self.escola.cadastrar_materia("matemática", self.prof, "80")

    def test_professor_e_materia(self):
        self.assertEqual(self.prof.nome, "Carlos de Lima")
        self.assertEqual(self.prof.matricula, "PROF000001")
        self.assertEqual(self.materia.nome, "Matemática")
        self.assertEqual(self.materia.id, 1)
        with self.assertRaises(ErroCadastro):
            self.escola.cadastrar_materia("MATEMÁTICA", self.prof, "40")
        with self.assertRaises(ErroCadastro):
            self.escola.cadastrar_materia("Física", None, "40")
        with self.assertRaises(ErroCadastro):
            self.escola.cadastrar_materia("Física", self.prof, "0")

    def test_matricula_professor_nao_repete_apos_exclusao(self):
        p2 = self.escola.cadastrar_professor("Ana Paula")
        p3 = self.escola.cadastrar_professor("Rui Costa")
        self.escola.excluir_professor(p2)
        p4 = self.escola.cadastrar_professor("Lia Matos")
        self.assertEqual(p3.matricula, "PROF000003")
        self.assertEqual(p4.matricula, "PROF000004")

    def test_boletim_aprovado(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "70,5", "90"], "8")
        self.assertAlmostEqual(b.media, 80.1666, places=3)
        self.assertAlmostEqual(b.frequencia, 90.0)
        self.assertEqual(b.situacao, "Aprovado")
        self.assertEqual(b.notas_formatadas(), "80 / 70.5 / 90")

    def test_boletim_reprovado(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["50", "40", "60"], "0")
        self.assertEqual(b.situacao, "Reprovado por nota")
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["90", "90", "90"], "30")
        self.assertEqual(b.situacao, "Reprovado por falta")
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["10", "10", "10"], "80")
        self.assertEqual(b.situacao, "Reprovado por nota e falta")

    def test_lancar_de_novo_substitui(self):
        self.escola.lancar_boletim(self.aluno, self.materia, ["10", "10", "10"], "0")
        self.escola.lancar_boletim(self.aluno, self.materia, ["100", "100", "100"], "0")
        self.assertEqual(len(self.escola.boletins), 1)
        self.assertEqual(self.escola.boletins[0].media, 100)

    def test_boletim_invalido(self):
        casos = [
            (["101", "0", "0"], "0"), (["-1", "0", "0"], "0"),
            (["abc", "0", "0"], "0"), (["nan", "0", "0"], "0"),
            (["", "0", "0"], "0"), (["50", "50", "50"], "81"),
            (["50", "50", "50"], "-1"), (["50", "50", "50"], "x"),
        ]
        for notas, faltas in casos:
            with self.subTest(notas=notas, faltas=faltas):
                with self.assertRaises(ErroCadastro):
                    self.escola.lancar_boletim(self.aluno, self.materia, notas, faltas)
        self.assertEqual(self.escola.boletins, [])

    def test_exclusoes_respeitam_vinculos(self):
        self.escola.lancar_boletim(self.aluno, self.materia, ["70", "70", "70"], "0")
        with self.assertRaises(ErroCadastro):
            self.escola.excluir_professor(self.prof)
        with self.assertRaises(ErroCadastro):
            self.escola.excluir_materia(self.materia)
        self.escola.excluir_aluno(self.aluno)          # leva os boletins junto
        self.assertEqual(self.escola.boletins, [])
        self.escola.excluir_materia(self.materia)
        self.escola.excluir_professor(self.prof)
        self.assertEqual((self.escola.materias, self.escola.professores), ([], []))


class TestePersistencia(unittest.TestCase):
    def test_salvar_e_carregar(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "dados.json")
            e1 = Escola(caminho)
            aluno = e1.cadastrar_aluno(**dados_aluno())
            prof = e1.cadastrar_professor("Carlos Lima")
            materia = e1.cadastrar_materia("Física", prof, "60")
            e1.lancar_boletim(aluno, materia, ["70", "80", "90"], "5")

            e2 = Escola(caminho)
            self.assertEqual(e2.alunos[0].to_dict(), aluno.to_dict())
            self.assertEqual(e2.materias[0].professor.nome, "Carlos Lima")
            b = e2.boletins[0]
            self.assertIs(b.aluno, e2.alunos[0])
            self.assertIs(b.materia, e2.materias[0])
            self.assertEqual(b.situacao, "Aprovado")
            # ids/matrículas continuam de onde pararam
            self.assertEqual(e2.cadastrar_professor("Rui Costa").matricula, "PROF000002")

    def test_arquivo_corrompido_nao_derruba(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "dados.json")
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("{isso não é json")
            escola = Escola(caminho)
            self.assertEqual(escola.alunos, [])
            self.assertTrue(os.path.exists(caminho + ".corrompido"))


if __name__ == "__main__":
    unittest.main()
