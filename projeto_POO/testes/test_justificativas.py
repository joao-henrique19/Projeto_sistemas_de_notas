import os
import tempfile
import unittest

from escola import Escola, ErroCadastro
from formatacoes.mascaras import (
    mascara_cpf, mascara_cep, mascara_data, mascara_telefone,
)
from testes.test_escola import dados_aluno


class BaseJustificativas(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.docs = os.path.join(self.pasta.name, "documentos")
        self.escola = Escola(pasta_documentos=self.docs)
        self.aluno = self.escola.cadastrar_aluno(**dados_aluno())
        self.prof = self.escola.cadastrar_professor("Carlos Lima")
        self.materia = self.escola.cadastrar_materia("Matemática", self.prof, "80")

    def criar_arquivo(self, nome="atestado.pdf", conteudo=b"%PDF-1.4 teste"):
        caminho = os.path.join(self.pasta.name, nome)
        with open(caminho, "wb") as f:
            f.write(conteudo)
        return caminho

    def justificar(self, **extra):
        dados = dict(
            aluno=self.aluno, materia=self.materia, data_falta="10/03/2026",
            horas="10", motivo="Atestado médico", descricao="",
        )
        dados.update(extra)
        return self.escola.cadastrar_justificativa(**dados)


class TesteCadastroJustificativa(BaseJustificativas):
    def test_cadastro_basico_fica_pendente(self):
        j = self.justificar()
        self.assertEqual(j.status, "Pendente")
        self.assertEqual(j.horas, 10)
        self.assertFalse(j.tem_documento)
        self.assertEqual(self.escola.justificativas, [j])

    def test_cadastro_com_documento_copia_o_arquivo(self):
        origem = self.criar_arquivo()
        j = self.justificar(arquivo_origem=origem)
        self.assertTrue(j.tem_documento)
        self.assertEqual(j.arquivo_original, "atestado.pdf")
        caminho = self.escola.caminho_documento(j)
        self.assertTrue(os.path.isfile(caminho))
        self.assertTrue(os.path.isfile(origem))   # o original não é movido
        self.assertTrue(j.arquivo.startswith(self.aluno.matricula))

    def test_campos_invalidos(self):
        invalidos = [
            dict(aluno=None), dict(materia=None),
            dict(data_falta="31/02/2026"), dict(data_falta="01/01/2999"),
            dict(horas="0"), dict(horas="81"), dict(horas="x"), dict(horas=""),
            dict(motivo="Porque sim"), dict(motivo="Outro", descricao=""),
        ]
        for extra in invalidos:
            with self.subTest(extra=extra):
                with self.assertRaises(ErroCadastro):
                    self.justificar(**extra)
        self.assertEqual(self.escola.justificativas, [])

    def test_motivo_outro_com_descricao(self):
        j = self.justificar(motivo="Outro", descricao="Enchente na rua")
        self.assertEqual(j.descricao, "Enchente na rua")

    def test_documento_invalido_nao_cria_justificativa(self):
        casos = {
            "virus.exe": b"abc",
            "vazio.pdf": b"",
            "grande.pdf": b"x" * (5 * 1024 * 1024 + 1),
        }
        for nome, conteudo in casos.items():
            with self.subTest(nome=nome):
                origem = self.criar_arquivo(nome, conteudo)
                with self.assertRaises(ErroCadastro):
                    self.justificar(arquivo_origem=origem)
        with self.assertRaises(ErroCadastro):
            self.justificar(arquivo_origem=os.path.join(self.pasta.name, "nao_existe.pdf"))
        self.assertEqual(self.escola.justificativas, [])
        self.assertEqual(os.listdir(self.docs) if os.path.isdir(self.docs) else [], [])

    def test_trocar_documento_apaga_o_antigo(self):
        j = self.justificar(arquivo_origem=self.criar_arquivo("a.pdf"))
        antigo = self.escola.caminho_documento(j)
        self.escola.anexar_documento(j, self.criar_arquivo("b.png", b"png"))
        self.assertEqual(j.arquivo_original, "b.png")
        self.assertFalse(os.path.exists(antigo))
        self.assertTrue(os.path.isfile(self.escola.caminho_documento(j)))

    def test_buscar(self):
        self.justificar()
        self.justificar(motivo="Consulta ou exame", horas="4")
        self.assertEqual(len(self.escola.buscar_justificativas("")), 2)
        self.assertEqual(len(self.escola.buscar_justificativas("consulta")), 1)
        self.assertEqual(len(self.escola.buscar_justificativas("joão")), 2)
        self.assertEqual(len(self.escola.buscar_justificativas("", "Deferida")), 0)


class TesteAnaliseEFrequencia(BaseJustificativas):
    def test_deferir_abona_faltas_no_boletim(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "30")
        self.assertEqual(b.situacao, "Reprovado por falta")     # 62,5% de frequência
        j = self.justificar(horas="20")

        self.escola.analisar_justificativa(j, "Deferida", "Atestado válido")
        self.assertEqual(j.parecer, "Atestado válido")
        self.assertNotEqual(j.data_analise, "")
        self.assertEqual(b.faltas_abonadas, 20)
        self.assertEqual(b.faltas_efetivas, 10)
        self.assertAlmostEqual(b.frequencia, 87.5)
        self.assertEqual(b.situacao, "Aprovado")

    def test_pendente_e_indeferida_nao_abonam(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "30")
        j = self.justificar(horas="20")
        self.assertAlmostEqual(b.frequencia, 62.5)               # pendente
        with self.assertRaises(ErroCadastro):                    # exige parecer
            self.escola.analisar_justificativa(j, "Indeferida", "  ")
        self.escola.analisar_justificativa(j, "Indeferida", "Sem documento")
        self.assertAlmostEqual(b.frequencia, 62.5)

    def test_reverter_decisao_desfaz_o_abono(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "30")
        j = self.justificar(horas="20")
        self.escola.analisar_justificativa(j, "Deferida")
        self.escola.analisar_justificativa(j, "Pendente")
        self.assertEqual(b.faltas_abonadas, 0)
        self.assertEqual(j.data_analise, "")

    def test_abono_maior_que_as_faltas_nao_passa_de_100(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "5")
        j = self.justificar(horas="40")
        self.escola.analisar_justificativa(j, "Deferida")
        self.assertEqual(b.faltas_efetivas, 0)
        self.assertEqual(b.faltas_abonadas, 5)
        self.assertAlmostEqual(b.frequencia, 100)

    def test_justificativa_deferida_vale_para_boletim_lancado_depois(self):
        j = self.justificar(horas="20")
        self.escola.analisar_justificativa(j, "Deferida")
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "30")
        self.assertEqual(b.faltas_abonadas, 20)

    def test_varias_justificativas_somam(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "30")
        for horas in ("8", "12"):
            self.escola.analisar_justificativa(self.justificar(horas=horas), "Deferida")
        self.assertEqual(b.faltas_abonadas, 20)

    def test_excluir_justificativa_remove_arquivo_e_abono(self):
        b = self.escola.lancar_boletim(self.aluno, self.materia, ["80", "80", "80"], "30")
        j = self.justificar(horas="20", arquivo_origem=self.criar_arquivo())
        caminho = self.escola.caminho_documento(j)
        self.escola.analisar_justificativa(j, "Deferida")
        self.escola.excluir_justificativa(j)
        self.assertFalse(os.path.exists(caminho))
        self.assertEqual(b.faltas_abonadas, 0)

    def test_vinculos_na_exclusao(self):
        j = self.justificar(arquivo_origem=self.criar_arquivo())
        caminho = self.escola.caminho_documento(j)
        with self.assertRaises(ErroCadastro):
            self.escola.excluir_materia(self.materia)
        self.escola.excluir_aluno(self.aluno)    # leva a justificativa e o arquivo
        self.assertEqual(self.escola.justificativas, [])
        self.assertFalse(os.path.exists(caminho))
        self.escola.excluir_materia(self.materia)


class TestePersistenciaJustificativas(unittest.TestCase):
    def test_salvar_e_carregar(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "dados.json")
            origem = os.path.join(pasta, "laudo.pdf")
            with open(origem, "wb") as f:
                f.write(b"%PDF")

            e1 = Escola(caminho)
            aluno = e1.cadastrar_aluno(**dados_aluno())
            prof = e1.cadastrar_professor("Carlos Lima")
            materia = e1.cadastrar_materia("Física", prof, "60")
            e1.lancar_boletim(aluno, materia, ["70", "80", "90"], "20")
            j = e1.cadastrar_justificativa(
                aluno, materia, "05/03/2026", "15", "Atestado médico",
                "Gripe", origem,
            )
            e1.analisar_justificativa(j, "Deferida", "ok")

            self.assertTrue(os.path.isdir(os.path.join(pasta, "documentos")))
            e2 = Escola(caminho)
            j2 = e2.justificativas[0]
            self.assertEqual(j2.to_dict(), j.to_dict())
            self.assertIs(j2.aluno, e2.alunos[0])
            self.assertIs(j2.materia, e2.materias[0])
            self.assertTrue(os.path.isfile(e2.caminho_documento(j2)))
            self.assertEqual(e2.boletins[0].faltas_abonadas, 15)   # abono volta ao carregar

    def test_arquivo_antigo_sem_justificativas_continua_abrindo(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "dados.json")
            e1 = Escola(caminho)
            e1.cadastrar_aluno(**dados_aluno())
            import json
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
            del dados["justificativas"]
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(dados, f)
            e2 = Escola(caminho)
            self.assertEqual(len(e2.alunos), 1)
            self.assertEqual(e2.justificativas, [])


class TesteMascaras(unittest.TestCase):
    def test_mascaras(self):
        self.assertEqual(mascara_cpf("52998224725"), "529.982.247-25")
        self.assertEqual(mascara_cpf("5299"), "529.9")
        self.assertEqual(mascara_cpf("abc529.982.247-25999"), "529.982.247-25")
        self.assertEqual(mascara_cep("58300000"), "58300-000")
        self.assertEqual(mascara_cep("583"), "583")
        self.assertEqual(mascara_data("15032008"), "15/03/2008")
        self.assertEqual(mascara_data("1503"), "15/03")
        self.assertEqual(mascara_telefone("83912345678"), "(83) 9 1234-5678")
        self.assertEqual(mascara_telefone("8332345678"), "(83) 3234-5678")
        self.assertEqual(mascara_telefone("8"), "(8")
        self.assertEqual(mascara_telefone(""), "")

    def test_mascara_e_aceita_pelo_cadastro(self):
        escola = Escola()
        aluno = escola.cadastrar_aluno(**dados_aluno(
            cpf=mascara_cpf("52998224725"), telefone=mascara_telefone("83912345678"),
            cep=mascara_cep("58300000"), data_nascimento=mascara_data("15032008"),
        ))
        self.assertEqual(aluno.cpf, "529.982.247-25")


if __name__ == "__main__":
    unittest.main()
