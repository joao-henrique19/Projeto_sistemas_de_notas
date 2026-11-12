"""Páginas de professores, matérias e notas/faltas."""
import tkinter as tk

from academico.boletim import MEDIA_MINIMA, FREQUENCIA_MINIMA
from escola import ErroCadastro
from interface.base import PaginaLista
from interface.componentes import Dialogo, Formulario, confirmar
from interface.tema import T
from validacoes.validar_dados import converter_nota


# =================================================================== PROFESSORES
class PaginaProfessores(PaginaLista):
    titulo = "Professores"
    subtitulo = "Quem leciona cada matéria."
    texto_novo = "Novo professor"
    texto_vazio = "Nenhum professor cadastrado ainda."
    nome_singular = "professor"
    nome_plural = "professores"
    colunas = [
        ("matricula", "Matrícula", 130, "w"), ("nome", "Nome", 280, "w"),
        ("materias", "Matérias que leciona", 380, "w"),
    ]

    def acoes(self):
        return [("Excluir", self.excluir, "perigo")]

    def itens(self):
        texto = self.texto_busca().strip().casefold()
        for professor in self.escola.professores:
            nomes = ", ".join(m.nome for m in self.escola.materias_do_professor(professor))
            if texto and texto not in (professor.nome + professor.matricula + nomes).casefold():
                continue
            yield (professor.matricula, professor,
                   (professor.matricula, professor.nome, nomes or "—"), None)

    def novo(self):
        dialogo = Dialogo(self.app, "Novo professor", largura=460,
                          subtitulo="A matrícula é gerada automaticamente.")
        f = Formulario(dialogo.corpo)
        f.linha(("nome", "Nome completo", "texto"), pady=(0, 4))
        f.campo("nome").focar()

        def salvar():
            dialogo.limpar_erro()
            try:
                professor = self.escola.cadastrar_professor(f.valor("nome"))
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            dialogo.destroy()
            self.app.atualizar_tudo()
            self.app.notificar("Professor cadastrado. Matrícula " + professor.matricula)

        dialogo.botoes("Cadastrar professor", salvar)
        dialogo.ao_apertar_enter(salvar)
        dialogo.exibir()

    def excluir(self):
        professor = self.objeto()
        if professor is None:
            return
        if not confirmar(self.app, "Excluir professor",
                         "Excluir o professor " + professor.nome + "?", "Excluir", perigo=True):
            return
        try:
            self.escola.excluir_professor(professor)
        except ErroCadastro as erro:
            self.app.notificar(str(erro), "erro", 5200)
            return
        self.app.atualizar_tudo()
        self.app.notificar("Professor excluído.", "info")


# ===================================================================== MATÉRIAS
class PaginaMaterias(PaginaLista):
    titulo = "Matérias"
    subtitulo = "Disciplinas, professores responsáveis e carga horária."
    texto_novo = "Nova matéria"
    texto_vazio = "Nenhuma matéria cadastrada ainda."
    nome_singular = "matéria"
    nome_plural = "matérias"
    colunas = [
        ("id", "Código", 80, "w"), ("nome", "Matéria", 260, "w"),
        ("professor", "Professor", 260, "w"), ("carga", "Carga horária", 120, "w"),
    ]

    def acoes(self):
        return [("Excluir", self.excluir, "perigo")]

    def itens(self):
        texto = self.texto_busca().strip().casefold()
        for m in self.escola.materias:
            if texto and texto not in (m.nome + m.professor.nome).casefold():
                continue
            yield (str(m.id), m, (m.id, m.nome, m.professor.nome,
                                  str(m.carga_horaria) + " h"), None)

    def novo(self):
        professores = list(self.escola.professores)
        if not professores:
            self.app.notificar("Cadastre um professor antes de criar matérias.", "aviso", 4500)
            return
        dialogo = Dialogo(self.app, "Nova matéria", largura=520)
        f = Formulario(dialogo.corpo)
        f.linha(("nome", "Nome da matéria", "texto"))
        f.linha(("professor", "Professor", "combo",
                 {"valores": [p.matricula + " - " + p.nome for p in professores], "peso": 2}),
                ("carga", "Carga horária (h)", "texto"), pady=(0, 4))
        f.campo("nome").focar()

        def salvar():
            dialogo.limpar_erro()
            posicao = f.indice("professor")
            professor = professores[posicao] if posicao >= 0 else None
            try:
                materia = self.escola.cadastrar_materia(f.valor("nome"), professor, f.valor("carga"))
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            dialogo.destroy()
            self.app.atualizar_tudo()
            self.app.notificar("Matéria “" + materia.nome + "” cadastrada.")

        dialogo.botoes("Cadastrar matéria", salvar)
        dialogo.ao_apertar_enter(salvar)
        dialogo.exibir()

    def excluir(self):
        materia = self.objeto()
        if materia is None:
            return
        if not confirmar(self.app, "Excluir matéria",
                         "Excluir a matéria " + materia.nome + "?", "Excluir", perigo=True):
            return
        try:
            self.escola.excluir_materia(materia)
        except ErroCadastro as erro:
            self.app.notificar(str(erro), "erro", 5200)
            return
        self.app.atualizar_tudo()
        self.app.notificar("Matéria excluída.", "info")


# ================================================================ NOTAS E FALTAS
class PaginaNotas(PaginaLista):
    titulo = "Notas e faltas"
    subtitulo = "Lance as notas e as faltas. Faltas com justificativa deferida são abonadas."
    texto_novo = "Lançar notas"
    texto_vazio = "Nenhum boletim lançado ainda."
    nome_singular = "boletim"
    nome_plural = "boletins"
    colunas = [
        ("aluno", "Aluno", 190, "w"), ("materia", "Matéria", 140, "w"),
        ("notas", "Notas", 120, "w"), ("media", "Média", 70, "center"),
        ("faltas", "Faltas", 70, "center"), ("abonadas", "Abonadas", 90, "center"),
        ("freq", "Freq.", 70, "center"), ("situacao", "Situação", 170, "w"),
    ]

    def acoes(self):
        return [
            ("Editar", self.editar, "secundario"),
            ("Excluir", self.excluir, "perigo"),
        ]

    def itens(self):
        texto = self.texto_busca().strip().casefold()
        for posicao, b in enumerate(self.escola.boletins):
            if texto and texto not in (b.aluno.nome + b.materia.nome + b.situacao).casefold():
                continue
            if b.aprovado:
                tag = "ok"
            elif b.media >= MEDIA_MINIMA or b.frequencia >= FREQUENCIA_MINIMA:
                tag = "aviso"
            else:
                tag = "erro"
            abonadas = ("+" + str(b.faltas_abonadas)) if b.faltas_abonadas else "—"
            yield (str(posicao), b, (
                b.aluno.nome, b.materia.nome, b.notas_formatadas(),
                format(b.media, ".1f"), b.faltas, abonadas,
                format(b.frequencia, ".0f") + "%", b.situacao,
            ), tag)

    def novo(self):
        self._formulario(None)

    def editar(self):
        boletim = self.objeto()
        if boletim is not None:
            self._formulario(boletim)

    def _formulario(self, boletim):
        alunos = list(self.escola.alunos)
        materias = list(self.escola.materias)
        if not alunos or not materias:
            self.app.notificar("Cadastre ao menos um aluno e uma matéria primeiro.", "aviso", 4500)
            return

        editando = boletim is not None
        dialogo = Dialogo(
            self.app, "Editar notas" if editando else "Lançar notas e faltas", largura=600,
            subtitulo="Notas de 0 a 100. Lançar de novo para o mesmo aluno e matéria "
                      "substitui o boletim anterior.",
        )
        f = Formulario(dialogo.corpo)
        f.linha(("aluno", "Aluno", "combo",
                 {"valores": [a.matricula + " - " + a.nome for a in alunos]}))
        f.linha(("materia", "Matéria", "combo",
                 {"valores": [str(m.id) + " - " + m.nome for m in materias], "peso": 2}),
                ("faltas", "Faltas (em horas)", "texto"))
        f.linha(("nota1", "Nota 1", "texto"), ("nota2", "Nota 2", "texto"),
                ("nota3", "Nota 3", "texto"))

        # prévia ao vivo
        previa = tk.Frame(dialogo.corpo, bg=T["superficie_alt"])
        previa.pack(fill="x", pady=(2, 0))
        rotulo_previa = tk.Label(previa, bg=T["superficie_alt"], fg=T["suave"],
                                 font=T.fonte(10), justify="left", anchor="w",
                                 padx=16, pady=12, wraplength=520)
        rotulo_previa.pack(fill="x")

        def atualizar_previa(*_):
            ia, im = f.indice("aluno"), f.indice("materia")
            notas = [converter_nota(f.valor(k)) for k in ("nota1", "nota2", "nota3")]
            faltas = f.valor("faltas").strip()
            if im < 0 or None in notas or not faltas.isdecimal():
                rotulo_previa.configure(
                    text="Prévia: preencha matéria, notas e faltas para ver a situação.",
                    fg=T["suave"])
                return
            materia = materias[im]
            faltas = int(faltas)
            if faltas > materia.carga_horaria:
                rotulo_previa.configure(
                    text="As faltas não podem passar de " + str(materia.carga_horaria) + " horas.",
                    fg=T["perigo"])
                return
            abonadas = 0
            if ia >= 0:
                abonadas = min(faltas, self.escola.horas_justificadas(alunos[ia], materia))
            frequencia = (materia.carga_horaria - (faltas - abonadas)) / materia.carga_horaria * 100
            media = sum(notas) / 3
            reprovacoes = []
            if media < MEDIA_MINIMA:
                reprovacoes.append("nota")
            if frequencia < FREQUENCIA_MINIMA:
                reprovacoes.append("falta")
            situacao = "Aprovado" if not reprovacoes else "Reprovado por " + " e ".join(reprovacoes)
            texto = ("Prévia:  média " + format(media, ".1f") + "   ·   frequência "
                     + format(frequencia, ".0f") + "%   ·   " + situacao)
            if abonadas:
                texto += "\n" + str(abonadas) + " h de falta abonadas por justificativa deferida."
            rotulo_previa.configure(text=texto, fg=T["sucesso"] if not reprovacoes else T["perigo"])

        for chave in ("nota1", "nota2", "nota3", "faltas"):
            f.campo(chave).var.trace_add("write", atualizar_previa)
        f.campo("aluno").ao_escolher(atualizar_previa)
        f.campo("materia").ao_escolher(atualizar_previa)

        if editando:
            f.campo("aluno").definir_indice(alunos.index(boletim.aluno))
            f.campo("materia").definir_indice(materias.index(boletim.materia))
            for numero, nota in enumerate(boletim.notas, start=1):
                f.definir("nota" + str(numero), format(nota, "g"))
            f.definir("faltas", str(boletim.faltas))
            f.campo("aluno").travar()       # editar não troca aluno nem matéria
            f.campo("materia").travar()
        atualizar_previa()

        def salvar():
            dialogo.limpar_erro()
            ia, im = f.indice("aluno"), f.indice("materia")
            aluno = alunos[ia] if ia >= 0 else None
            materia = materias[im] if im >= 0 else None
            if (not editando and aluno and materia
                    and self.escola.buscar_boletim(aluno, materia) is not None):
                if not confirmar(dialogo, "Boletim já existe",
                                 "Esse aluno já tem boletim nessa matéria. Substituir?",
                                 "Substituir"):
                    return
            notas = [f.valor("nota1"), f.valor("nota2"), f.valor("nota3")]
            try:
                resultado = self.escola.lancar_boletim(aluno, materia, notas, f.valor("faltas"))
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            dialogo.destroy()
            self.app.atualizar_tudo()
            self.app.notificar(
                resultado.aluno.nome + " · " + resultado.materia.nome + ": média "
                + format(resultado.media, ".1f") + " — " + resultado.situacao,
                "sucesso" if resultado.aprovado else "aviso")

        dialogo.botoes("Salvar boletim", salvar)
        dialogo.ao_apertar_enter(salvar)
        dialogo.exibir()

    def excluir(self):
        boletim = self.objeto()
        if boletim is None:
            return
        if confirmar(self.app, "Excluir boletim",
                     "Excluir o boletim de " + boletim.aluno.nome + " em "
                     + boletim.materia.nome + "?", "Excluir", perigo=True):
            self.escola.excluir_boletim(boletim)
            self.app.atualizar_tudo()
            self.app.notificar("Boletim excluído.", "info")
