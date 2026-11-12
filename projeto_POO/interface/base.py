"""Classes-base das páginas: Pagina (qualquer tela) e PaginaLista (tabela + ações)."""
import tkinter as tk

from interface.componentes import Botao, Busca, Cartao, Tabela
from interface.tema import T


class Pagina(tk.Frame):
    """Uma tela do sistema. `atualizar()` redesenha com os dados atuais."""
    titulo = ""
    subtitulo = ""

    def __init__(self, pai, app):
        super().__init__(pai, bg=T["fundo"])
        self.app = app
        self.escola = app.escola
        self.conteudo = tk.Frame(self, bg=T["fundo"])
        self.conteudo.pack(fill="both", expand=True, padx=36, pady=(0, 28))

    def atualizar(self):
        pass


class PaginaLista(Pagina):
    """Barra superior (busca + botão de novo), tabela e botões de ação.

    Cada página filha define `colunas`, `itens()` e as ações.
    """
    colunas = []
    texto_novo = "Novo"
    texto_vazio = "Nada por aqui ainda."
    nome_singular = "item"
    nome_plural = "itens"
    com_busca = True

    def __init__(self, pai, app):
        super().__init__(pai, app)
        self._objetos = {}

        self.barra = tk.Frame(self.conteudo, bg=T["fundo"])
        self.barra.pack(fill="x", pady=(0, 16))
        self.busca = None
        if self.com_busca:
            self.busca = Busca(self.barra, self.atualizar)
            self.busca.pack(side="left")
        self.montar_barra(self.barra)
        Botao(self.barra, "+  " + self.texto_novo, self.novo, "primario").pack(side="right")

        cartao = Cartao(self.conteudo, padx=0, pady=0)
        cartao.pack(fill="both", expand=True)
        self.tabela = Tabela(
            cartao.corpo, self.colunas, ao_abrir=self.abrir,
            ao_selecionar=self._selecionou, texto_vazio=self.texto_vazio,
        )
        self.tabela.pack(fill="both", expand=True)

        rodape = tk.Frame(self.conteudo, bg=T["fundo"])
        rodape.pack(fill="x", pady=(14, 0))
        self.rotulo_total = tk.Label(rodape, bg=T["fundo"], fg=T["suave"], font=T.fonte(10))
        self.rotulo_total.pack(side="right")
        self._botoes = []
        for texto, comando, variante in self.acoes():
            botao = Botao(rodape, texto, comando, variante)
            botao.pack(side="left", padx=(0, 10))
            botao.habilitar(False)
            self._botoes.append(botao)

    # -- ganchos para as páginas filhas
    def montar_barra(self, barra):
        """Permite acrescentar widgets (ex.: filtros) à barra superior."""

    def acoes(self):
        """[(texto, comando, variante)] — ficam ativos só com uma linha selecionada."""
        return []

    def itens(self):
        """Devolve [(iid, objeto, valores, tag)]."""
        return []

    def novo(self):
        pass

    def abrir(self):
        pass

    # -- funcionamento
    def texto_busca(self):
        return self.busca.texto() if self.busca else ""

    def objeto(self):
        """Objeto da linha selecionada (ou None)."""
        return self._objetos.get(self.tabela.selecionado())

    def _selecionou(self, iid):
        for botao in self._botoes:
            botao.habilitar(iid is not None)

    def atualizar(self):
        self._objetos = {}
        linhas = []
        for iid, objeto, valores, tag in self.itens():
            self._objetos[iid] = objeto
            linhas.append((iid, valores, tag))
        if self.texto_busca() and not linhas:
            self.tabela.definir_texto_vazio("Nenhum resultado para essa busca.")
        else:
            self.tabela.definir_texto_vazio(self.texto_vazio)
        self.tabela.preencher(linhas)
        total = len(linhas)
        self.rotulo_total.configure(text=str(total) + " " + (
            self.nome_singular if total == 1 else self.nome_plural))
