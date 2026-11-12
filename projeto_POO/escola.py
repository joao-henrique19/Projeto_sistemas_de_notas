"""Regras de negócio do sistema escolar (sem nenhuma dependência de interface)."""
import json
import os
import shutil
import uuid

from alunos.aluno import Aluno
from alunos.matricula import gerar_matricula
from academico.professor import Professor
from academico.materia import Materia
from academico.boletim import Boletim
from academico.justificativa import (
    Justificativa, MOTIVOS, STATUS, STATUS_PENDENTE, STATUS_DEFERIDA,
    STATUS_INDEFERIDA, EXTENSOES_PERMITIDAS, TAMANHO_MAXIMO, hoje_formatado,
)
from formatacoes.formatar_dados import formatar_cpf, formatar_nome
from formatacoes.gerar_email import gerar_email
from validacoes.validar_contato import validar_telefone, validar_cep
from validacoes.validar_dados import (
    validar_nome, validar_cpf, validar_data_nascimento, validar_data_passada,
    normalizar_curso, normalizar_serie, converter_nota,
)
from validacoes.validar_endereco import validar_texto, validar_numero

ARQUIVO_PADRAO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dados.json"
)


class ErroCadastro(ValueError):
    """Erro de validação com mensagem pronta para mostrar ao usuário."""


class Escola:
    def __init__(self, arquivo=None, pasta_documentos=None):
        self.arquivo = arquivo
        if pasta_documentos is None and arquivo:
            pasta_documentos = os.path.join(
                os.path.dirname(os.path.abspath(arquivo)), "documentos"
            )
        self.pasta_documentos = pasta_documentos
        self.alunos = []
        self.professores = []
        self.materias = []
        self.boletins = []
        self.justificativas = []
        self.carregar()

    # ------------------------------------------------------------ alunos
    def cadastrar_aluno(self, nacionalidade, nome, data_nascimento, cpf,
                        telefone, cep, rua, numero, bairro, cidade,
                        curso, serie):
        nacionalidade = nacionalidade.strip()
        nome = nome.strip()
        data_nascimento = data_nascimento.strip()
        cpf = cpf.strip()
        telefone = telefone.strip()
        cep = cep.strip()
        rua = rua.strip()
        numero = numero.strip()
        bairro = bairro.strip()
        cidade = cidade.strip()

        if not validar_nome(nacionalidade):
            raise ErroCadastro("Nacionalidade inválida.")
        if not validar_nome(nome):
            raise ErroCadastro(
                "Nome inválido. Use apenas letras (mínimo de 3 caracteres)."
            )
        if not validar_data_nascimento(data_nascimento):
            raise ErroCadastro(
                "Data de nascimento inválida. Use DD/MM/AAAA e uma data que já passou."
            )
        if not validar_cpf(cpf):
            raise ErroCadastro("CPF inválido.")
        cpf_formatado = formatar_cpf(cpf)
        if any(aluno.cpf == cpf_formatado for aluno in self.alunos):
            raise ErroCadastro("Já existe um aluno cadastrado com esse CPF.")
        if not validar_telefone(telefone):
            raise ErroCadastro("Telefone inválido. Use DDD + número (10 ou 11 dígitos).")
        if not validar_cep(cep):
            raise ErroCadastro("CEP inválido. Use 8 dígitos.")
        if not validar_texto(rua):
            raise ErroCadastro("Rua inválida.")
        if not validar_numero(numero):
            raise ErroCadastro("Número inválido. Digite apenas números ou S/N.")
        if not validar_texto(bairro):
            raise ErroCadastro("Bairro inválido.")
        if not validar_texto(cidade):
            raise ErroCadastro("Cidade inválida.")

        curso_oficial = normalizar_curso(curso)
        if curso_oficial is None:
            raise ErroCadastro("Selecione um curso.")
        serie_oficial = normalizar_serie(serie)
        if serie_oficial is None:
            raise ErroCadastro("Selecione uma série.")

        matricula = gerar_matricula(
            curso_oficial, [aluno.matricula for aluno in self.alunos]
        )
        email = gerar_email(
            formatar_nome(nome), [aluno.email for aluno in self.alunos]
        )
        aluno = Aluno(
            nacionalidade, nome, data_nascimento, cpf, telefone, cep, rua,
            numero, bairro, cidade, curso_oficial, serie_oficial,
            matricula, email,
        )
        self.alunos.append(aluno)
        self.salvar()
        return aluno

    def excluir_aluno(self, aluno):
        """Remove o aluno e também os boletins e justificativas dele."""
        self.boletins = [b for b in self.boletins if b.aluno is not aluno]
        dele = [j for j in self.justificativas if j.aluno is aluno]
        self.justificativas = [j for j in self.justificativas if j.aluno is not aluno]
        self.alunos.remove(aluno)
        self.salvar()
        for justificativa in dele:
            self._apagar_arquivo(justificativa.arquivo)

    def buscar_alunos(self, texto):
        texto = texto.strip().casefold()
        if texto == "":
            return list(self.alunos)
        resultado = []
        for aluno in self.alunos:
            campos = (aluno.nome, aluno.matricula, aluno.cpf, aluno.curso, aluno.serie)
            if any(texto in campo.casefold() for campo in campos):
                resultado.append(aluno)
        return resultado

    # -------------------------------------------------------- professores
    def cadastrar_professor(self, nome):
        nome = nome.strip()
        if not validar_nome(nome):
            raise ErroCadastro(
                "Nome inválido. Use apenas letras (mínimo de 3 caracteres)."
            )
        nome = formatar_nome(nome)
        numeros = [int(p.matricula[4:]) for p in self.professores]
        matricula = "PROF" + str(max(numeros, default=0) + 1).zfill(6)
        professor = Professor(nome, matricula)
        self.professores.append(professor)
        self.salvar()
        return professor

    def materias_do_professor(self, professor):
        return [m for m in self.materias if m.professor is professor]

    def excluir_professor(self, professor):
        if self.materias_do_professor(professor):
            raise ErroCadastro(
                "Esse professor leciona matérias cadastradas. "
                "Exclua ou troque essas matérias antes."
            )
        self.professores.remove(professor)
        self.salvar()

    # ----------------------------------------------------------- matérias
    def cadastrar_materia(self, nome, professor, carga_horaria):
        nome = nome.strip()
        if not validar_texto(nome):
            raise ErroCadastro("Nome da matéria inválido.")
        if professor is None or professor not in self.professores:
            raise ErroCadastro("Selecione um professor.")
        carga = str(carga_horaria).strip()
        if not carga.isdecimal() or int(carga) <= 0:
            raise ErroCadastro(
                "A carga horária deve ser um número inteiro maior que zero."
            )
        nome = nome.title()
        if any(m.nome.casefold() == nome.casefold() for m in self.materias):
            raise ErroCadastro("Já existe uma matéria com esse nome.")

        novo_id = max((m.id for m in self.materias), default=0) + 1
        materia = Materia(novo_id, nome, professor, int(carga))
        self.materias.append(materia)
        self.salvar()
        return materia

    def excluir_materia(self, materia):
        if any(b.materia is materia for b in self.boletins):
            raise ErroCadastro(
                "Essa matéria já tem notas lançadas. Exclua os boletins dela antes."
            )
        if any(j.materia is materia for j in self.justificativas):
            raise ErroCadastro(
                "Essa matéria tem justificativas de falta. "
                "Exclua as justificativas dela antes."
            )
        self.materias.remove(materia)
        self.salvar()

    # ----------------------------------------------------------- boletins
    def buscar_boletim(self, aluno, materia):
        for boletim in self.boletins:
            if boletim.aluno is aluno and boletim.materia is materia:
                return boletim
        return None

    def lancar_boletim(self, aluno, materia, notas, faltas):
        """Cria o boletim (ou substitui o que já existe para aluno + matéria)."""
        if aluno is None or aluno not in self.alunos:
            raise ErroCadastro("Selecione um aluno.")
        if materia is None or materia not in self.materias:
            raise ErroCadastro("Selecione uma matéria.")

        valores = []
        for numero, texto in enumerate(notas, start=1):
            nota = converter_nota(texto)
            if nota is None:
                raise ErroCadastro(
                    "Nota " + str(numero) + " inválida. Digite um número de 0 a 100."
                )
            valores.append(nota)

        faltas = str(faltas).strip()
        if not faltas.isdecimal() or int(faltas) > materia.carga_horaria:
            raise ErroCadastro(
                "Faltas inválidas. Digite um número inteiro entre 0 e "
                + str(materia.carga_horaria) + "."
            )

        existente = self.buscar_boletim(aluno, materia)
        if existente is not None:
            self.boletins.remove(existente)
        boletim = Boletim(aluno, materia, valores, int(faltas))
        self.boletins.append(boletim)
        self._sincronizar_justificadas()
        self.salvar()
        return boletim

    def excluir_boletim(self, boletim):
        self.boletins.remove(boletim)
        self.salvar()

    # ----------------------------------------------------- justificativas
    def horas_justificadas(self, aluno, materia):
        """Total de horas com justificativa deferida (aluno + matéria)."""
        return sum(
            j.horas for j in self.justificativas
            if j.aluno is aluno and j.materia is materia and j.deferida
        )

    def _sincronizar_justificadas(self):
        """Atualiza em cada boletim quantas horas foram abonadas."""
        for boletim in self.boletins:
            boletim.faltas_justificadas = self.horas_justificadas(
                boletim.aluno, boletim.materia
            )

    def justificativas_do_aluno(self, aluno):
        return [j for j in self.justificativas if j.aluno is aluno]

    def contar_justificativas(self, status):
        return sum(1 for j in self.justificativas if j.status == status)

    def buscar_justificativas(self, texto="", status=None):
        texto = texto.strip().casefold()
        resultado = []
        for j in self.justificativas:
            if status and j.status != status:
                continue
            campos = (j.aluno.nome, j.aluno.matricula, j.materia.nome,
                      j.motivo, j.data_falta, j.arquivo_original, j.status)
            if texto == "" or any(texto in campo.casefold() for campo in campos):
                resultado.append(j)
        return resultado

    def cadastrar_justificativa(self, aluno, materia, data_falta, horas,
                                motivo, descricao="", arquivo_origem=None):
        if aluno is None or aluno not in self.alunos:
            raise ErroCadastro("Selecione um aluno.")
        if materia is None or materia not in self.materias:
            raise ErroCadastro("Selecione uma matéria.")

        data_falta = data_falta.strip()
        if not validar_data_passada(data_falta):
            raise ErroCadastro(
                "Data da falta inválida. Use DD/MM/AAAA e uma data que já passou."
            )
        horas = str(horas).strip()
        if not horas.isdecimal() or not 1 <= int(horas) <= materia.carga_horaria:
            raise ErroCadastro(
                "As horas devem ser um número inteiro entre 1 e "
                + str(materia.carga_horaria) + " (carga horária da matéria)."
            )
        if motivo not in MOTIVOS:
            raise ErroCadastro("Selecione o motivo da falta.")
        descricao = descricao.strip()
        if motivo == "Outro" and not descricao:
            raise ErroCadastro('Para o motivo "Outro", descreva o que aconteceu.')

        novo_id = max((j.id for j in self.justificativas), default=0) + 1
        justificativa = Justificativa(
            novo_id, aluno, materia, data_falta, int(horas), motivo, descricao
        )
        if arquivo_origem:
            self._copiar_documento(justificativa, arquivo_origem)
        self.justificativas.append(justificativa)
        try:
            self.salvar()
        except ErroCadastro:
            self.justificativas.remove(justificativa)
            self._apagar_arquivo(justificativa.arquivo)
            raise
        return justificativa

    def anexar_documento(self, justificativa, arquivo_origem):
        """Anexa (ou troca) o documento de uma justificativa já cadastrada."""
        if justificativa not in self.justificativas:
            raise ErroCadastro("Justificativa não encontrada.")
        anterior = (justificativa.arquivo, justificativa.arquivo_original)
        self._copiar_documento(justificativa, arquivo_origem)
        try:
            self.salvar()
        except ErroCadastro:
            self._apagar_arquivo(justificativa.arquivo)
            justificativa.arquivo, justificativa.arquivo_original = anterior
            raise
        self._apagar_arquivo(anterior[0])

    def caminho_documento(self, justificativa):
        """Caminho do documento no disco, ou None se não houver / sumiu."""
        if not justificativa.arquivo or not self.pasta_documentos:
            return None
        caminho = os.path.join(self.pasta_documentos, justificativa.arquivo)
        return caminho if os.path.isfile(caminho) else None

    def analisar_justificativa(self, justificativa, status, parecer=""):
        """Defere, indefere ou volta a justificativa para Pendente."""
        if justificativa not in self.justificativas:
            raise ErroCadastro("Justificativa não encontrada.")
        if status not in STATUS:
            raise ErroCadastro("Situação inválida.")
        parecer = parecer.strip()
        if status == STATUS_INDEFERIDA and not parecer:
            raise ErroCadastro("Explique o motivo do indeferimento no campo de parecer.")
        justificativa.status = status
        justificativa.parecer = parecer
        justificativa.data_analise = "" if status == STATUS_PENDENTE else hoje_formatado()
        self._sincronizar_justificadas()
        self.salvar()

    def excluir_justificativa(self, justificativa):
        self.justificativas.remove(justificativa)
        self._sincronizar_justificadas()
        self.salvar()
        self._apagar_arquivo(justificativa.arquivo)

    # -- arquivos
    def _copiar_documento(self, justificativa, origem):
        """Valida e copia o arquivo para a pasta de documentos."""
        if not self.pasta_documentos:
            raise ErroCadastro("Nenhuma pasta de documentos configurada.")
        if not origem or not os.path.isfile(origem):
            raise ErroCadastro("O arquivo escolhido não foi encontrado.")
        nome_original = os.path.basename(origem)
        extensao = os.path.splitext(nome_original)[1].lower()
        if extensao not in EXTENSOES_PERMITIDAS:
            raise ErroCadastro(
                "Tipo de arquivo não permitido. Use: "
                + ", ".join(e.upper().lstrip(".") for e in EXTENSOES_PERMITIDAS) + "."
            )
        tamanho = os.path.getsize(origem)
        if tamanho == 0:
            raise ErroCadastro("O arquivo escolhido está vazio.")
        if tamanho > TAMANHO_MAXIMO:
            raise ErroCadastro(
                "Arquivo muito grande. O máximo é "
                + str(TAMANHO_MAXIMO // (1024 * 1024)) + " MB."
            )
        nome_guardado = "{}_{}_{}{}".format(
            justificativa.aluno.matricula, justificativa.id,
            uuid.uuid4().hex[:8], extensao,
        )
        try:
            os.makedirs(self.pasta_documentos, exist_ok=True)
            shutil.copy2(origem, os.path.join(self.pasta_documentos, nome_guardado))
        except OSError as erro:
            raise ErroCadastro("Não foi possível guardar o documento: " + str(erro))
        justificativa.arquivo = nome_guardado
        justificativa.arquivo_original = nome_original

    def _apagar_arquivo(self, nome_guardado):
        if not nome_guardado or not self.pasta_documentos:
            return
        try:
            os.remove(os.path.join(self.pasta_documentos, nome_guardado))
        except OSError:
            pass

    # -------------------------------------------------------- persistência
    def salvar(self):
        if not self.arquivo:
            return
        dados = {
            "alunos": [a.to_dict() for a in self.alunos],
            "professores": [p.to_dict() for p in self.professores],
            "materias": [m.to_dict() for m in self.materias],
            "boletins": [b.to_dict() for b in self.boletins],
            "justificativas": [j.to_dict() for j in self.justificativas],
        }
        temporario = self.arquivo + ".tmp"
        try:
            with open(temporario, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            os.replace(temporario, self.arquivo)
        except OSError as erro:
            raise ErroCadastro("Não foi possível salvar os dados: " + str(erro))

    def carregar(self):
        if not self.arquivo or not os.path.exists(self.arquivo):
            return
        try:
            with open(self.arquivo, encoding="utf-8") as f:
                dados = json.load(f)

            alunos = [Aluno.from_dict(d) for d in dados.get("alunos", [])]
            professores = [Professor.from_dict(d) for d in dados.get("professores", [])]
            por_matricula = {p.matricula: p for p in professores}
            materias = [
                Materia.from_dict(d, por_matricula[d["professor"]])
                for d in dados.get("materias", [])
            ]
            alunos_por_matricula = {a.matricula: a for a in alunos}
            materias_por_id = {m.id: m for m in materias}
            boletins = [
                Boletim.from_dict(
                    d, alunos_por_matricula[d["aluno"]], materias_por_id[d["materia"]]
                )
                for d in dados.get("boletins", [])
            ]
            justificativas = [
                Justificativa.from_dict(
                    d, alunos_por_matricula[d["aluno"]], materias_por_id[d["materia"]]
                )
                for d in dados.get("justificativas", [])
            ]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # Arquivo ilegível: guarda uma cópia e começa do zero, sem apagar nada.
            try:
                os.replace(self.arquivo, self.arquivo + ".corrompido")
            except OSError:
                pass
            return

        self.alunos = alunos
        self.professores = professores
        self.materias = materias
        self.boletins = boletins
        self.justificativas = justificativas
        self._sincronizar_justificadas()
