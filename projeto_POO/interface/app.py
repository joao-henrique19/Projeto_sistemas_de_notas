"""Janela principal do Sistema Escolar (tkinter): barra lateral + páginas."""
import tkinter as tk
from datetime import date

from academico.justificativa import STATUS_PENDENTE
from escola import Escola, ARQUIVO_PADRAO
from interface.componentes import Notificador
from interface.pagina_academico import PaginaMaterias, PaginaNotas, PaginaProfessores
from interface.pagina_alunos import PaginaAlunos
from interface.pagina_inicio import PaginaInicio
from interface.pagina_justificativas import PaginaJustificativas
from interface.tema import T, aplicar_estilos

# (chave, texto do menu, classe da página)
MENU = [
    ("inicio", "Visão geral", PaginaInicio),
    ("alunos", "Alunos", PaginaAlunos),
    ("professores", "Professores", PaginaProfessores),
    ("materias", "Matérias", PaginaMaterias),
    ("notas", "Notas e faltas", PaginaNotas),
    ("justificativas", "Justificativas", PaginaJustificativas),
]

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def data_por_extenso():
    hoje = date.today()
    return (DIAS[hoje.weekday()].capitalize() + ", " + str(hoje.day) + " de "
            + MESES[hoje.month - 1] + " de " + str(hoje.year))


class ItemMenu(tk.Frame):
    """Item da barra lateral: barra de destaque, efeito ao passar o mouse e contador."""

    def __init__(self, pai, texto, comando):
        super().__init__(pai, bg=T["sidebar"], cursor="hand2")
        self._ativo = False
        self._comando = comando
        self.barra = tk.Frame(self, width=4, bg=T["sidebar"])
        self.barra.pack(side="left", fill="y")
        self.rotulo = tk.Label(self, text=texto, anchor="w", bg=T["sidebar"],
                               fg=T["sidebar_texto"], font=T.fonte(11), padx=20, pady=12)
        self.rotulo.pack(side="left", fill="x", expand=True)
        self.contador = tk.Label(self, text="", bg=T["alerta"], fg="#1B1200",
                                 font=T.fonte(9, "bold"), padx=7, pady=1)
        for peca in (self, self.rotulo, self.barra, self.contador):
            peca.bind("<Enter>", lambda e: self._pintar(True))
            peca.bind("<Leave>", lambda e: self._pintar(False))
            peca.bind("<Button-1>", lambda e: self._comando())

    def _pintar(self, passando):
        if self._ativo:
            fundo, texto, barra = T["sidebar_ativo"], "#FFFFFF", T["sidebar_destaque"]
        elif passando:
            fundo, texto, barra = T["sidebar_hover"], "#FFFFFF", T["sidebar_hover"]
        else:
            fundo, texto, barra = T["sidebar"], T["sidebar_texto"], T["sidebar"]
        self.configure(bg=fundo)
        self.rotulo.configure(bg=fundo, fg=texto,
                              font=T.fonte(11, "bold" if self._ativo else "normal"))
        self.barra.configure(bg=barra)

    def ativar(self, ativo):
        self._ativo = ativo
        self._pintar(False)

    def definir_contador(self, quantidade):
        if quantidade > 0:
            self.contador.configure(text=str(quantidade))
            self.contador.pack(side="right", padx=(0, 16))
        else:
            self.contador.pack_forget()


class App(tk.Tk):
    def __init__(self, escola):
        super().__init__()
        self.escola = escola
        self.title("Sistema Escolar")
        self.geometry("1320x800")
        self.minsize(1120, 700)
        T.detectar_fonte(self)
        T.carregar()
        self.pagina_atual = "inicio"
        self.paginas = {}
        self.itens_menu = {}
        self.notificador = None
        self.construir()

    # --------------------------------------------------------------- layout
    def construir(self):
        """Monta (ou remonta, ao trocar o tema) toda a janela."""
        for filho in self.winfo_children():
            filho.destroy()
        self.configure(bg=T["fundo"])
        aplicar_estilos(self)
        self.notificador = Notificador(self)

        # barra lateral
        lateral = tk.Frame(self, bg=T["sidebar"], width=250)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        marca = tk.Frame(lateral, bg=T["sidebar"])
        marca.pack(fill="x", padx=24, pady=(30, 28))
        tk.Label(marca, text="Sistema Escolar", bg=T["sidebar"], fg="#FFFFFF",
                 font=T.fonte(16, "bold"), anchor="w").pack(fill="x")
        tk.Label(marca, text="Gestão acadêmica", bg=T["sidebar"], fg=T["sidebar_texto"],
                 font=T.fonte(10), anchor="w").pack(fill="x", pady=(2, 0))

        self.itens_menu = {}
        for chave, texto, _ in MENU:
            item = ItemMenu(lateral, texto, lambda c=chave: self.ir(c))
            item.pack(fill="x", pady=1)
            self.itens_menu[chave] = item

        rodape = tk.Frame(lateral, bg=T["sidebar"])
        rodape.pack(side="bottom", fill="x", pady=(0, 20))
        alternar = ItemMenu(
            rodape, "Modo escuro" if T.nome == "claro" else "Modo claro", self.alternar_tema)
        alternar.pack(fill="x")

        # área principal
        principal = tk.Frame(self, bg=T["fundo"])
        principal.pack(side="left", fill="both", expand=True)

        cabecalho = tk.Frame(principal, bg=T["fundo"])
        cabecalho.pack(fill="x", padx=36, pady=(30, 22))
        textos = tk.Frame(cabecalho, bg=T["fundo"])
        textos.pack(side="left")
        self.rotulo_titulo = tk.Label(textos, bg=T["fundo"], fg=T["texto"],
                                      font=T.fonte(22, "bold"), anchor="w")
        self.rotulo_titulo.pack(anchor="w")
        self.rotulo_subtitulo = tk.Label(textos, bg=T["fundo"], fg=T["suave"],
                                         font=T.fonte(11), anchor="w")
        self.rotulo_subtitulo.pack(anchor="w", pady=(3, 0))
        tk.Label(cabecalho, text=data_por_extenso(), bg=T["fundo"], fg=T["suave"],
                 font=T.fonte(10)).pack(side="right", anchor="n", pady=6)

        area = tk.Frame(principal, bg=T["fundo"])
        area.pack(fill="both", expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)

        self.paginas = {}
        for chave, _, classe in MENU:
            pagina = classe(area, self)
            pagina.grid(row=0, column=0, sticky="nsew")
            self.paginas[chave] = pagina

        self.atualizar_tudo()
        self.ir(self.pagina_atual)

    # ------------------------------------------------------------ navegação
    def pagina(self, chave):
        return self.paginas[chave]

    def ir(self, chave):
        self.pagina_atual = chave
        pagina = self.paginas[chave]
        pagina.atualizar()
        pagina.tkraise()
        self.rotulo_titulo.configure(text=pagina.titulo)
        self.rotulo_subtitulo.configure(text=pagina.subtitulo)
        for nome, item in self.itens_menu.items():
            item.ativar(nome == chave)

    def atualizar_tudo(self):
        for pagina in self.paginas.values():
            pagina.atualizar()
        self.itens_menu["justificativas"].definir_contador(
            self.escola.contar_justificativas(STATUS_PENDENTE))

    def alternar_tema(self):
        T.alternar()
        T.salvar()
        self.construir()

    def notificar(self, mensagem, tipo="sucesso", duracao=3600):
        self.notificador.mostrar(mensagem, tipo, duracao)


def iniciar():
    escola = Escola(ARQUIVO_PADRAO)
    App(escola).mainloop()
