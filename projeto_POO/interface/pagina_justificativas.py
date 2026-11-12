"""Página de justificativas de falta: envio de documento e análise."""
import os
import tkinter as tk

from academico.justificativa import (
    MOTIVOS, STATUS_PENDENTE, STATUS_DEFERIDA, STATUS_INDEFERIDA, hoje_formatado,
)
from escola import ErroCadastro
from interface.base import PaginaLista
from interface.componentes import (
    AreaArquivo, Botao, CampoMultilinha, Dialogo, Formulario, confirmar,
    escolher_arquivo, formatar_tamanho, rotulo_valor, selo,
)
from interface.sistema import abrir_arquivo
from interface.tema import T

TIPO_STATUS = {STATUS_PENDENTE: "aviso", STATUS_DEFERIDA: "sucesso", STATUS_INDEFERIDA: "erro"}
TAG_STATUS = {STATUS_PENDENTE: "aviso", STATUS_DEFERIDA: "ok", STATUS_INDEFERIDA: "erro"}
FILTROS = (
    ("Todas", None), ("Pendentes", STATUS_PENDENTE),
    ("Deferidas", STATUS_DEFERIDA), ("Indeferidas", STATUS_INDEFERIDA),
)


class PaginaJustificativas(PaginaLista):
    titulo = "Justificativas de falta"
    subtitulo = "Receba documentos, analise os pedidos e abone faltas justificadas."
    texto_novo = "Nova justificativa"
    texto_vazio = "Nenhuma justificativa por aqui. Clique em “Nova justificativa” para enviar uma."
    nome_singular = "justificativa"
    nome_plural = "justificativas"
    colunas = [
        ("id", "Nº", 50, "center"), ("data", "Data da falta", 105, "w"),
        ("aluno", "Aluno", 190, "w"), ("materia", "Matéria", 130, "w"),
        ("horas", "Horas", 60, "center"), ("motivo", "Motivo", 190, "w"),
        ("doc", "Documento", 110, "w"), ("status", "Situação", 120, "w"),
    ]

    # ------------------------------------------------------------- lista
    def montar_barra(self, barra):
        self.filtro = None
        self._chips = {}
        for texto, status in FILTROS:
            chip = Botao(barra, texto, lambda s=status: self.filtrar(s),
                         "chip_ativo" if status is None else "chip",
                         altura=34, tamanho=9)
            chip.pack(side="left", padx=(10, 0))
            self._chips[status] = chip

    def filtrar(self, status):
        self.filtro = status
        self.atualizar()

    def acoes(self):
        return [
            ("Ver e analisar", self.abrir, "secundario"),
            ("Abrir documento", self.abrir_documento, "secundario"),
            ("Excluir", self.excluir, "perigo"),
        ]

    def itens(self):
        for j in reversed(self.escola.buscar_justificativas(self.texto_busca(), self.filtro)):
            if not j.tem_documento:
                doc = "—"
            elif self.escola.caminho_documento(j) is None:
                doc = "Ausente"
            else:
                doc = "✓ Anexado"
            yield (str(j.id), j, (
                j.id, j.data_falta, j.aluno.nome, j.materia.nome, str(j.horas) + " h",
                j.motivo, doc, "● " + j.status,
            ), TAG_STATUS[j.status])

    def atualizar(self):
        super().atualizar()
        for status, chip in self._chips.items():
            if status is None:
                quantidade = len(self.escola.justificativas)
                texto = "Todas"
            else:
                quantidade = self.escola.contar_justificativas(status)
                texto = dict((s, t) for t, s in FILTROS)[status]
            chip.definir_texto(texto + "  " + str(quantidade))
            chip.definir_variante("chip_ativo" if status == self.filtro else "chip")

    # ----------------------------------------------------- nova justificativa
    def novo(self):
        self.nova()

    def nova(self, aluno=None):
        alunos = list(self.escola.alunos)
        materias = list(self.escola.materias)
        if not alunos or not materias:
            self.app.notificar("Cadastre ao menos um aluno e uma matéria primeiro.", "aviso", 4500)
            return

        dialogo = Dialogo(
            self.app, "Nova justificativa de falta", largura=660,
            subtitulo="Informe a falta e anexe o documento (atestado, declaração etc.). "
                      "O pedido fica pendente até ser analisado.",
        )
        f = Formulario(dialogo.corpo)
        f.linha(("aluno", "Aluno", "combo",
                 {"valores": [a.matricula + " - " + a.nome for a in alunos]}))
        f.linha(("materia", "Matéria", "combo",
                 {"valores": [str(m.id) + " - " + m.nome for m in materias], "peso": 3}),
                ("horas", "Horas faltadas", "texto", {"peso": 2}),
                ("data", "Data da falta", "data", {"peso": 2}))
        f.linha(("motivo", "Motivo", "combo", {"valores": MOTIVOS}))
        f.linha(("descricao", "Descrição (obrigatória se o motivo for “Outro”)", "area",
                 {"linhas": 3}))
        area = AreaArquivo(dialogo.corpo)
        area.pack(fill="x", pady=(0, 4))

        f.definir("data", hoje_formatado())
        if aluno is not None and aluno in alunos:
            f.campo("aluno").definir_indice(alunos.index(aluno))

        def enviar():
            dialogo.limpar_erro()
            ia, im = f.indice("aluno"), f.indice("materia")
            try:
                justificativa = self.escola.cadastrar_justificativa(
                    alunos[ia] if ia >= 0 else None,
                    materias[im] if im >= 0 else None,
                    f.valor("data"), f.valor("horas"), f.valor("motivo"),
                    f.valor("descricao"), area.valor() or None,
                )
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            dialogo.destroy()
            self.filtro = None
            self.app.atualizar_tudo()
            self.app.ir("justificativas")
            self.app.notificar(
                "Justificativa nº " + str(justificativa.id) + " enviada para análise"
                + (" com documento anexado." if justificativa.tem_documento else "."))

        dialogo.botoes("Enviar justificativa", enviar)
        dialogo.exibir()

    # -------------------------------------------------------- ver e analisar
    def _impacto(self, j):
        boletim = self.escola.buscar_boletim(j.aluno, j.materia)
        if boletim is None:
            return ("Ainda não há notas lançadas para este aluno nesta matéria. "
                    "Se for deferida, o abono vale assim que o boletim for lançado.")
        carga = j.materia.carga_horaria
        base = self.escola.horas_justificadas(j.aluno, j.materia) - (j.horas if j.deferida else 0)

        def frequencia(abono):
            return (carga - (boletim.faltas - min(boletim.faltas, abono))) / carga * 100

        return ("Frequência de " + j.aluno.nome.split()[0] + " em " + j.materia.nome + ":  "
                + format(frequencia(base), ".0f") + "% sem esta justificativa  →  "
                + format(frequencia(base + j.horas), ".0f") + "% se for deferida.")

    def abrir(self):
        j = self.objeto()
        if j is None:
            return
        dialogo = Dialogo(self.app, "Justificativa nº " + str(j.id), largura=720)

        # situação
        topo = tk.Frame(dialogo.corpo, bg=T["superficie"])
        topo.pack(fill="x", pady=(0, 14))
        selo(topo, j.status.upper(), TIPO_STATUS[j.status], tamanho=9).pack(side="left")
        info = "Enviada em " + j.data_envio
        if j.data_analise:
            info += "  ·  analisada em " + j.data_analise
        tk.Label(topo, text=info, bg=T["superficie"], fg=T["suave"],
                 font=T.fonte(10)).pack(side="left", padx=12)

        # dados
        grade = tk.Frame(dialogo.corpo, bg=T["superficie"])
        grade.pack(fill="x")
        dados = [
            ("Aluno", j.aluno.nome), ("Matéria", j.materia.nome),
            ("Data da falta", j.data_falta), ("Horas faltadas", str(j.horas) + " h"),
            ("Motivo", j.motivo), ("Curso / série", j.aluno.curso + " · " + j.aluno.serie),
        ]
        for posicao, (rotulo, valor) in enumerate(dados):
            grade.columnconfigure(posicao % 3, weight=1, uniform="d")
            rotulo_valor(grade, rotulo, valor, largura=200).grid(
                row=posicao // 3, column=posicao % 3, sticky="w", pady=(0, 12))
        if j.descricao:
            rotulo_valor(dialogo.corpo, "Descrição", j.descricao, largura=650).pack(
                fill="x", pady=(0, 12))

        # documento
        caixa = tk.Frame(dialogo.corpo, bg=T["superficie_alt"])
        caixa.pack(fill="x", pady=(0, 14))
        interno = tk.Frame(caixa, bg=T["superficie_alt"])
        interno.pack(fill="x", padx=16, pady=12)
        textos = tk.Frame(interno, bg=T["superficie_alt"])
        textos.pack(side="left", fill="x", expand=True)
        tk.Label(textos, text="DOCUMENTO", bg=T["superficie_alt"], fg=T["suave"],
                 font=T.fonte(8, "bold"), anchor="w").pack(fill="x")
        rotulo_doc = tk.Label(textos, bg=T["superficie_alt"], font=T.fonte(10, "bold"),
                              anchor="w", justify="left")
        rotulo_doc.pack(fill="x", pady=(2, 0))
        botao_abrir = Botao(interno, "Abrir", lambda: self.abrir_documento(j, dialogo),
                            "secundario", altura=32, tamanho=9)
        botao_anexar = Botao(interno, "", None, "secundario", altura=32, tamanho=9)

        def atualizar_documento():
            caminho = self.escola.caminho_documento(j)
            if caminho:
                rotulo_doc.configure(
                    text=j.arquivo_original + "  (" + formatar_tamanho(os.path.getsize(caminho)) + ")",
                    fg=T["texto"])
            elif j.tem_documento:
                rotulo_doc.configure(text="Arquivo não encontrado na pasta de documentos",
                                     fg=T["perigo"])
            else:
                rotulo_doc.configure(text="Nenhum documento anexado", fg=T["suave"])
            botao_abrir.habilitar(caminho is not None)
            botao_anexar.definir_texto("Trocar documento" if j.tem_documento else "Anexar documento")

        def anexar():
            origem = escolher_arquivo(dialogo)
            if not origem:
                return
            dialogo.limpar_erro()
            try:
                self.escola.anexar_documento(j, origem)
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            atualizar_documento()
            self.atualizar()

        botao_anexar.comando = anexar
        botao_anexar.pack(side="right")
        botao_abrir.pack(side="right", padx=(0, 8))
        atualizar_documento()

        # parecer
        parecer = CampoMultilinha(dialogo.corpo, "Parecer da análise (obrigatório para indeferir)",
                                  linhas=3)
        parecer.pack(fill="x")
        parecer.definir(j.parecer)
        tk.Label(dialogo.corpo, text=self._impacto(j), bg=T["superficie"], fg=T["info"],
                 font=T.fonte(10), anchor="w", justify="left", wraplength=660).pack(
            fill="x", pady=(10, 0))

        def decidir(status, mensagem, tipo):
            dialogo.limpar_erro()
            try:
                self.escola.analisar_justificativa(j, status, parecer.valor())
            except ErroCadastro as erro:
                dialogo.mostrar_erro(str(erro))
                return
            dialogo.destroy()
            self.app.atualizar_tudo()
            self.app.notificar(mensagem, tipo)

        Botao(dialogo.rodape, "Fechar", dialogo.destroy, "secundario").pack(side="left")
        Botao(dialogo.rodape, "Deferir", lambda: decidir(
            STATUS_DEFERIDA, "Justificativa deferida. As horas foram abonadas.", "sucesso"),
            "sucesso").pack(side="right")
        Botao(dialogo.rodape, "Indeferir", lambda: decidir(
            STATUS_INDEFERIDA, "Justificativa indeferida.", "aviso"),
            "perigo").pack(side="right", padx=(0, 10))
        if j.status != STATUS_PENDENTE:
            Botao(dialogo.rodape, "Voltar a pendente", lambda: decidir(
                STATUS_PENDENTE, "Justificativa voltou para pendente.", "info"),
                "fantasma").pack(side="right", padx=(0, 10))
        dialogo.exibir()

    # ----------------------------------------------------------------- ações
    def abrir_documento(self, justificativa=None, dialogo=None):
        j = justificativa or self.objeto()
        if j is None:
            return

        def avisar(texto, tipo):
            if dialogo is not None:
                dialogo.mostrar_erro(texto)
            else:
                self.app.notificar(texto, tipo, 4800)

        if not j.tem_documento:
            avisar("Esta justificativa não tem documento anexado.", "aviso")
            return
        caminho = self.escola.caminho_documento(j)
        if caminho is None:
            avisar("O arquivo não foi encontrado na pasta de documentos.", "erro")
            return
        try:
            abrir_arquivo(caminho)
        except OSError as erro:
            avisar("Não foi possível abrir o documento: " + str(erro), "erro")

    def excluir(self):
        j = self.objeto()
        if j is None:
            return
        aviso = ("Excluir a justificativa de " + j.aluno.nome + " em " + j.materia.nome
                 + " (falta de " + j.data_falta + ")?")
        if j.tem_documento:
            aviso += "\n\nO documento anexado também será apagado."
        if j.deferida:
            aviso += "\n\nAs " + str(j.horas) + " h abonadas voltarão a contar como falta."
        if confirmar(self.app, "Excluir justificativa", aviso, "Excluir", perigo=True):
            self.escola.excluir_justificativa(j)
            self.app.atualizar_tudo()
            self.app.notificar("Justificativa excluída.", "info")
