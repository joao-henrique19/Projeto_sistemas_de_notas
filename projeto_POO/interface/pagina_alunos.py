"""Página de alunos: lista, cadastro, detalhes e exclusão."""
import tkinter as tk

from escola import ErroCadastro
from interface.base import PaginaLista
from interface.componentes import (
    Botao, Dialogo, Formulario, confirmar, rotulo_valor, selo,
)
from interface.tema import T
from validacoes.validar_dados import CURSOS, SERIES

TIPO_STATUS = {"Pendente": "aviso", "Deferida": "sucesso", "Indeferida": "erro"}

CHAVES_ALUNO = (
    "nacionalidade", "nome", "data_nascimento", "cpf", "telefone", "cep",
    "rua", "numero", "bairro", "cidade", "curso", "serie",
)


class PaginaAlunos(PaginaLista):
    titulo = "Alunos"
    subtitulo = "Cadastre alunos e acompanhe a situação de cada um."
    texto_novo = "Novo aluno"
    texto_vazio = "Nenhum aluno cadastrado ainda. Clique em “Novo aluno” para começar."
    nome_singular = "aluno"
    nome_plural = "alunos"
    colunas = [
        ("matricula", "Matrícula", 120, "w"), ("nome", "Nome", 230, "w"),
        ("curso", "Curso", 140, "w"), ("serie", "Série", 80, "w"),
        ("cpf", "CPF", 125, "w"), ("email", "E-mail", 230, "w"),
    ]

    def acoes(self):
        return [
            ("Ver detalhes", self.abrir, "secundario"),
            ("Justificar falta", self.justificar, "secundario"),
            ("Excluir", self.excluir, "perigo"),
        ]

    def itens(self):
        for aluno in self.escola.buscar_alunos(self.texto_busca()):
            yield (aluno.matricula, aluno, (
                aluno.matricula, aluno.nome, aluno.curso, aluno.serie,
                aluno.cpf, aluno.email,
            ), None)

    # ------------------------------------------------------------- cadastro
    def novo(self):
        dialogo = Dialogo(
            self.app, "Novo aluno", largura=660,
            subtitulo="Preencha os dados. A matrícula e o e-mail são gerados automaticamente.",
        )
        f = Formulario(dialogo.corpo)
        f.linha(("nome", "Nome completo", "texto"))
        f.linha(("data_nascimento", "Data de nascimento", "data"), ("cpf", "CPF", "cpf"),
                ("telefone", "Telefone (com DDD)", "telefone"))
        f.linha(("rua", "Rua", "texto", {"peso": 3}), ("numero", "Número (ou S/N)", "texto"),
                ("cep", "CEP", "cep", {"peso": 2}))
        f.linha(("bairro", "Bairro", "texto"), ("cidade", "Cidade", "texto"))
        f.linha(("nacionalidade", "Nacionalidade", "texto"),
                ("curso", "Curso", "combo", {"valores": CURSOS}),
                ("serie", "Série", "combo", {"valores": SERIES}), pady=(0, 4))
        f.definir("nacionalidade", "Brasileira")
        f.campo("nome").focar()

        def salvar():
            dialogo.limpar_erro()
            dados = {chave: f.valor(chave) for chave in CHAVES_ALUNO}
            try:
                aluno = self.escola.cadastrar_aluno(**dados)
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            dialogo.destroy()
            self.app.atualizar_tudo()
            self.app.notificar("Aluno cadastrado. Matrícula " + aluno.matricula
                               + " · " + aluno.email)

        dialogo.botoes("Cadastrar aluno", salvar)
        dialogo.ao_apertar_enter(salvar)
        dialogo.exibir()

    # ------------------------------------------------------------- detalhes
    def abrir(self):
        aluno = self.objeto()
        if aluno is None:
            return
        dialogo = Dialogo(self.app, aluno.nome, largura=780,
                          subtitulo="Matrícula " + aluno.matricula + "  ·  " + aluno.email)

        grade = tk.Frame(dialogo.corpo, bg=T["superficie"])
        grade.pack(fill="x")
        campos = [
            ("Curso", aluno.curso), ("Série", aluno.serie),
            ("Nacionalidade", aluno.nacionalidade),
            ("Nascimento", aluno.data_nascimento), ("CPF", aluno.cpf),
            ("Telefone", aluno.telefone),
            ("Endereço", aluno.rua + ", " + aluno.numero), ("Bairro", aluno.bairro),
            ("Cidade / CEP", aluno.cidade + "  ·  " + aluno.cep),
        ]
        for posicao, (rotulo, valor) in enumerate(campos):
            grade.columnconfigure(posicao % 3, weight=1, uniform="d")
            rotulo_valor(grade, rotulo, valor, largura=210).grid(
                row=posicao // 3, column=posicao % 3, sticky="w", pady=(0, 12))

        boletins = [b for b in self.escola.boletins if b.aluno is aluno]
        self._secao(dialogo.corpo, "Notas e frequência", len(boletins))
        for boletim in boletins[:4]:
            linha = tk.Frame(dialogo.corpo, bg=T["superficie"])
            linha.pack(fill="x", pady=2)
            tk.Label(linha, text=boletim.materia.nome, bg=T["superficie"], fg=T["texto"],
                     font=T.fonte(10, "bold"), width=18, anchor="w").pack(side="left")
            tk.Label(linha, bg=T["superficie"], fg=T["suave"], font=T.fonte(10), anchor="w",
                     text="média " + format(boletim.media, ".1f")
                     + "  ·  frequência " + format(boletim.frequencia, ".0f") + "%").pack(
                side="left", padx=(0, 12))
            selo(linha, boletim.situacao, "sucesso" if boletim.aprovado else "erro").pack(side="right")
        self._mais(dialogo.corpo, len(boletins), 4)

        justificativas = self.escola.justificativas_do_aluno(aluno)
        self._secao(dialogo.corpo, "Justificativas de falta", len(justificativas))
        for j in justificativas[-4:][::-1]:
            linha = tk.Frame(dialogo.corpo, bg=T["superficie"])
            linha.pack(fill="x", pady=2)
            tk.Label(linha, text=j.data_falta, bg=T["superficie"], fg=T["texto"],
                     font=T.fonte(10, "bold"), width=12, anchor="w").pack(side="left")
            tk.Label(linha, bg=T["superficie"], fg=T["suave"], font=T.fonte(10), anchor="w",
                     text=j.materia.nome + "  ·  " + str(j.horas) + " h  ·  " + j.motivo).pack(
                side="left")
            selo(linha, j.status, TIPO_STATUS[j.status]).pack(side="right")
        self._mais(dialogo.corpo, len(justificativas), 4)

        def justificar():
            dialogo.destroy()
            self.app.pagina("justificativas").nova(aluno=aluno)

        Botao(dialogo.rodape, "Fechar", dialogo.destroy, "primario").pack(side="right")
        Botao(dialogo.rodape, "Justificar falta", justificar, "secundario").pack(
            side="right", padx=(0, 10))
        dialogo.exibir()

    def _secao(self, pai, titulo, quantidade):
        cab = tk.Frame(pai, bg=T["superficie"])
        cab.pack(fill="x", pady=(10, 4))
        tk.Frame(cab, bg=T["borda"], height=1).pack(fill="x", pady=(0, 10))
        tk.Label(cab, text=titulo, bg=T["superficie"], fg=T["texto"],
                 font=T.fonte(11, "bold")).pack(side="left")
        if quantidade == 0:
            tk.Label(cab, text="nenhum registro", bg=T["superficie"], fg=T["suave"],
                     font=T.fonte(10)).pack(side="left", padx=10)

    def _mais(self, pai, total, mostrados):
        if total > mostrados:
            tk.Label(pai, text="+ " + str(total - mostrados) + " mais (veja na página própria)",
                     bg=T["superficie"], fg=T["suave"], font=T.fonte(9)).pack(anchor="w")

    # ----------------------------------------------------------------- ações
    def justificar(self):
        aluno = self.objeto()
        if aluno is not None:
            self.app.pagina("justificativas").nova(aluno=aluno)

    def excluir(self):
        aluno = self.objeto()
        if aluno is None:
            return
        boletins = sum(1 for b in self.escola.boletins if b.aluno is aluno)
        justificativas = len(self.escola.justificativas_do_aluno(aluno))
        aviso = "Excluir o aluno " + aluno.nome + "?"
        if boletins or justificativas:
            aviso += "\n\nTambém serão excluídos: " + str(boletins) + " boletim(ns) e " \
                     + str(justificativas) + " justificativa(s) com seus documentos."
        if confirmar(self.app, "Excluir aluno", aviso, "Excluir", perigo=True):
            self.escola.excluir_aluno(aluno)
            self.app.atualizar_tudo()
            self.app.notificar("Aluno excluído.", "info")
