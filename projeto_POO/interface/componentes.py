"""Componentes visuais reutilizáveis (botões, campos, tabela, avisos, diálogos)."""
import os
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import font as tkfont

from formatacoes.mascaras import (
    mascara_cpf, mascara_cep, mascara_data, mascara_telefone,
)
from interface.tema import T

MASCARAS = {
    "cpf": mascara_cpf, "cep": mascara_cep,
    "data": mascara_data, "telefone": mascara_telefone,
}


# ------------------------------------------------------------------ utilidades
def abreviar(texto, limite):
    return texto if len(texto) <= limite else texto[:limite - 1] + "…"


def formatar_tamanho(bytes_):
    if bytes_ < 1024:
        return str(bytes_) + " B"
    if bytes_ < 1024 * 1024:
        return format(bytes_ / 1024, ".0f") + " KB"
    return format(bytes_ / (1024 * 1024), ".1f") + " MB"


def retangulo_arredondado(canvas, x1, y1, x2, y2, raio, **opcoes):
    pontos = [
        x1 + raio, y1, x2 - raio, y1, x2, y1, x2, y1 + raio,
        x2, y2 - raio, x2, y2, x2 - raio, y2, x1 + raio, y2,
        x1, y2, x1, y2 - raio, x1, y1 + raio, x1, y1,
    ]
    return canvas.create_polygon(pontos, smooth=True, **opcoes)


def cores_do_tipo(tipo):
    """(cor forte, cor de fundo suave) para sucesso / erro / aviso / info."""
    mapa = {
        "sucesso": ("sucesso", "sucesso_fundo"),
        "erro": ("perigo", "perigo_fundo"),
        "aviso": ("alerta", "alerta_fundo"),
        "info": ("info", "info_fundo"),
    }
    forte, suave = mapa.get(tipo, mapa["info"])
    return T[forte], T[suave]


# ---------------------------------------------------------------------- botão
def _estilo_botao(variante):
    c = T.cores
    estilos = {
        "primario": dict(bg=c["primaria"], hover=c["primaria_hover"], press=c["primaria_press"],
                         fg=c["sobre_primaria"], borda=c["primaria"]),
        "sucesso": dict(bg="#16A34A", hover="#15803D", press="#166534",
                        fg="#FFFFFF", borda="#16A34A"),
        "perigo": dict(bg=c["perigo_fundo"], hover=c["perigo"], press=c["perigo"],
                       fg=c["perigo"], fg_hover="#FFFFFF", borda=c["perigo_fundo"]),
        "secundario": dict(bg=c["superficie"], hover=c["superficie_alt"], press=c["borda"],
                           fg=c["texto"], borda=c["campo_borda"]),
        "fantasma": dict(bg=None, hover=c["superficie_alt"], press=c["borda"],
                         fg=c["suave"], fg_hover=c["texto"], borda=None),
        "chip": dict(bg=c["superficie"], hover=c["superficie_alt"], press=c["borda"],
                     fg=c["suave"], borda=c["campo_borda"]),
        "chip_ativo": dict(bg=c["primaria_suave"], hover=c["primaria_suave"],
                           press=c["primaria_suave"], fg=c["primaria"], borda=c["primaria"]),
    }
    return estilos[variante]


class Botao(tk.Canvas):
    """Botão com cantos arredondados, efeito ao passar o mouse e ao clicar."""

    def __init__(self, pai, texto, comando=None, variante="primario",
                 largura=None, altura=38, tamanho=10):
        super().__init__(pai, height=altura, highlightthickness=0, bd=0,
                         bg=pai.cget("bg"), cursor="hand2")
        self.texto = texto
        self.comando = comando
        self.variante = variante
        self.altura = altura
        self._fonte = T.fonte(tamanho, "bold")
        self._largura_fixa = largura
        self._habilitado = True
        self._hover = False
        self._pressionado = False
        self._ajustar_largura()
        self.bind("<Configure>", lambda e: self._desenhar())
        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._sair)
        self.bind("<ButtonPress-1>", self._apertar)
        self.bind("<ButtonRelease-1>", self._soltar)

    def _ajustar_largura(self):
        medida = tkfont.Font(font=self._fonte).measure(self.texto)
        self._largura_min = self._largura_fixa or medida + 36
        self.configure(width=self._largura_min)

    def _desenhar(self):
        self.delete("all")
        est = _estilo_botao(self.variante)
        largura = max(self.winfo_width(), self._largura_min)
        altura = self.altura
        if not self._habilitado:
            fundo, fg, borda = T["superficie_alt"], T["suave"], T["borda"]
            if est["bg"] is None:
                fundo = None
        elif self._pressionado:
            fundo, fg, borda = est["press"], est.get("fg_hover", est["fg"]), est["borda"]
        elif self._hover:
            fundo, fg, borda = est["hover"], est.get("fg_hover", est["fg"]), est["borda"]
        else:
            fundo, fg, borda = est["bg"], est["fg"], est["borda"]
        if fundo is not None:
            retangulo_arredondado(
                self, 1, 1, largura - 1, altura - 1, 10,
                fill=fundo, outline=borda or fundo,
            )
        self.create_text(largura / 2, altura / 2, text=self.texto, fill=fg, font=self._fonte)

    def _entrar(self, _):
        self._hover = True
        self._desenhar()

    def _sair(self, _):
        self._hover = False
        self._pressionado = False
        self._desenhar()

    def _apertar(self, _):
        if self._habilitado:
            self._pressionado = True
            self._desenhar()

    def _soltar(self, evento):
        era_pressionado = self._pressionado
        self._pressionado = False
        self._desenhar()
        dentro = 0 <= evento.x <= self.winfo_width() and 0 <= evento.y <= self.altura
        if era_pressionado and dentro and self._habilitado and self.comando:
            self.comando()

    # -- controle externo
    def habilitar(self, habilitado):
        self._habilitado = bool(habilitado)
        self.configure(cursor="hand2" if habilitado else "arrow")
        self._desenhar()

    def definir_texto(self, texto):
        self.texto = texto
        self._ajustar_largura()
        self._desenhar()

    def definir_variante(self, variante):
        self.variante = variante
        self._desenhar()


# ------------------------------------------------------------------- contêineres
class Cartao(tk.Frame):
    """Cartão com borda fina. Coloque o conteúdo em `.corpo`."""

    def __init__(self, pai, padx=20, pady=18):
        super().__init__(pai, bg=T["superficie"], highlightthickness=1,
                         highlightbackground=T["borda"], highlightcolor=T["borda"])
        self.corpo = tk.Frame(self, bg=T["superficie"])
        self.corpo.pack(fill="both", expand=True, padx=padx, pady=pady)


def selo(pai, texto, tipo="info", tamanho=9):
    """Etiqueta colorida (ex.: situação da justificativa)."""
    forte, suave = cores_do_tipo(tipo)
    return tk.Label(pai, text=texto, bg=suave, fg=forte, font=T.fonte(tamanho, "bold"),
                    padx=10, pady=3)


# ------------------------------------------------------------------------ campos
class CampoTexto(tk.Frame):
    """Rótulo + caixa de texto com borda que acende ao receber o foco."""

    def __init__(self, pai, rotulo, mascara=None):
        super().__init__(pai, bg=pai.cget("bg"))
        tk.Label(self, text=rotulo, anchor="w", bg=pai.cget("bg"), fg=T["suave"],
                 font=T.fonte(9, "bold")).pack(fill="x")
        self.var = tk.StringVar()
        self._moldura = tk.Frame(self, bg=T["campo_borda"])
        self._moldura.pack(fill="x", pady=(5, 0))
        interno = tk.Frame(self._moldura, bg=T["campo"])
        interno.pack(fill="x", padx=1, pady=1)
        self.entrada = tk.Entry(
            interno, textvariable=self.var, relief="flat", bd=0, width=8,
            bg=T["campo"], fg=T["texto"], insertbackground=T["texto"],
            font=T.fonte(10), highlightthickness=0,
        )
        self.entrada.pack(fill="x", padx=10, ipady=7)
        self.entrada.bind("<FocusIn>", lambda e: self._moldura.configure(bg=T["primaria"]))
        self.entrada.bind("<FocusOut>", lambda e: self._moldura.configure(bg=T["campo_borda"]))
        self._mascara = mascara
        if mascara:
            self.var.trace_add("write", self._aplicar_mascara)

    def _aplicar_mascara(self, *_):
        atual = self.var.get()
        novo = self._mascara(atual)
        if novo != atual:
            self.var.set(novo)
            self.entrada.icursor("end")

    def valor(self):
        return self.var.get()

    def definir(self, valor):
        self.var.set(valor)

    def limpar(self):
        self.var.set("")

    def focar(self):
        self.entrada.focus_set()


class CampoCombo(tk.Frame):
    """Rótulo + lista de opções. Use `indice()` para mapear a objetos."""

    def __init__(self, pai, rotulo, valores=()):
        super().__init__(pai, bg=pai.cget("bg"))
        tk.Label(self, text=rotulo, anchor="w", bg=pai.cget("bg"), fg=T["suave"],
                 font=T.fonte(9, "bold")).pack(fill="x")
        self.combo = ttk.Combobox(
            self, values=list(valores), state="readonly", style="Moderno.TCombobox",
            font=T.fonte(10), width=8,
        )
        self.combo.pack(fill="x", pady=(5, 0))
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.combo.selection_clear())

    def valor(self):
        return self.combo.get()

    def indice(self):
        return self.combo.current()

    def definir(self, valor):
        self.combo.set(valor)

    def definir_indice(self, posicao):
        if 0 <= posicao < len(self.combo["values"]):
            self.combo.current(posicao)

    def limpar(self):
        self.combo.set("")

    def travar(self):
        self.combo.configure(state="disabled")

    def definir_valores(self, valores):
        """Troca as opções mantendo a escolha atual, se ela ainda existir."""
        atual = self.combo.get()
        self.combo["values"] = list(valores)
        if atual not in valores:
            self.combo.set("")

    def ao_escolher(self, funcao):
        self.combo.bind("<<ComboboxSelected>>", lambda e: (self.combo.selection_clear(), funcao()), add="+")


class CampoMultilinha(tk.Frame):
    def __init__(self, pai, rotulo, linhas=3):
        super().__init__(pai, bg=pai.cget("bg"))
        tk.Label(self, text=rotulo, anchor="w", bg=pai.cget("bg"), fg=T["suave"],
                 font=T.fonte(9, "bold")).pack(fill="x")
        self._moldura = tk.Frame(self, bg=T["campo_borda"])
        self._moldura.pack(fill="x", pady=(5, 0))
        self.texto = tk.Text(
            self._moldura, height=linhas, width=8, wrap="word", relief="flat", bd=0,
            bg=T["campo"], fg=T["texto"], insertbackground=T["texto"],
            font=T.fonte(10), highlightthickness=0, padx=10, pady=8,
        )
        self.texto.pack(fill="x", padx=1, pady=1)
        self.texto.bind("<FocusIn>", lambda e: self._moldura.configure(bg=T["primaria"]))
        self.texto.bind("<FocusOut>", lambda e: self._moldura.configure(bg=T["campo_borda"]))

    def valor(self):
        return self.texto.get("1.0", "end").strip()

    def definir(self, valor):
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", valor)

    def limpar(self):
        self.texto.delete("1.0", "end")

    def ao_mudar(self, funcao):
        self.texto.bind("<KeyRelease>", lambda e: funcao())


class Formulario:
    """Monta campos em linhas (várias colunas por linha) e guarda por chave."""

    def __init__(self, pai):
        self.pai = pai
        self.campos = {}

    def linha(self, *especificacoes, pady=(0, 14)):
        """Cada especificação: (chave, rótulo, tipo[, extras]).

        tipo: texto | cpf | telefone | cep | data | combo | area
        extras: {"valores": [...], "peso": 2, "linhas": 3}
        """
        quadro = tk.Frame(self.pai, bg=self.pai.cget("bg"))
        quadro.pack(fill="x", pady=pady)
        for posicao, especificacao in enumerate(especificacoes):
            chave, rotulo, tipo = especificacao[:3]
            extras = especificacao[3] if len(especificacao) > 3 else {}
            quadro.columnconfigure(posicao, weight=extras.get("peso", 1), uniform="col")
            if tipo == "combo":
                campo = CampoCombo(quadro, rotulo, extras.get("valores", ()))
            elif tipo == "area":
                campo = CampoMultilinha(quadro, rotulo, extras.get("linhas", 3))
            else:
                campo = CampoTexto(quadro, rotulo, MASCARAS.get(tipo))
            campo.grid(row=0, column=posicao, sticky="new",
                       padx=(0 if posicao == 0 else 14, 0))
            self.campos[chave] = campo
        return quadro

    def campo(self, chave):
        return self.campos[chave]

    def valor(self, chave):
        return self.campos[chave].valor()

    def indice(self, chave):
        return self.campos[chave].indice()

    def definir(self, chave, valor):
        self.campos[chave].definir(valor)


class Busca(tk.Frame):
    """Caixa de busca que avisa a cada letra digitada."""

    def __init__(self, pai, ao_mudar, largura=34, dica="Buscar"):
        super().__init__(pai, bg=T["campo_borda"])
        interno = tk.Frame(self, bg=T["campo"])
        interno.pack(padx=1, pady=1, fill="both")
        tk.Label(interno, text=dica, bg=T["campo"], fg=T["suave"],
                 font=T.fonte(10)).pack(side="left", padx=(12, 4))
        self.var = tk.StringVar()
        self.entrada = tk.Entry(
            interno, textvariable=self.var, relief="flat", bd=0, width=largura,
            bg=T["campo"], fg=T["texto"], insertbackground=T["texto"],
            font=T.fonte(10), highlightthickness=0,
        )
        self.entrada.pack(side="left", ipady=8, padx=(0, 10))
        self.entrada.bind("<FocusIn>", lambda e: self.configure(bg=T["primaria"]))
        self.entrada.bind("<FocusOut>", lambda e: self.configure(bg=T["campo_borda"]))
        self.var.trace_add("write", lambda *args: ao_mudar())

    def texto(self):
        return self.var.get()


def escolher_arquivo(pai):
    """Abre o seletor de arquivos e devolve o caminho ('' se cancelar)."""
    return filedialog.askopenfilename(
        parent=pai.winfo_toplevel(), title="Escolher documento",
        filetypes=[
            ("Documentos e imagens", ("*.pdf", "*.png", "*.jpg", "*.jpeg", "*.doc", "*.docx")),
            ("Todos os arquivos", "*.*"),
        ],
    )


class AreaArquivo(tk.Frame):
    """Área tracejada para escolher o documento (clique para abrir o seletor)."""
    ALTURA = 86

    def __init__(self, pai, rotulo="Documento comprobatório (opcional)", ao_mudar=None):
        super().__init__(pai, bg=pai.cget("bg"))
        tk.Label(self, text=rotulo, anchor="w", bg=pai.cget("bg"), fg=T["suave"],
                 font=T.fonte(9, "bold")).pack(fill="x")
        self.caminho = ""
        self._hover = False
        self._ao_mudar = ao_mudar
        self.tela = tk.Canvas(self, height=self.ALTURA, bg=T["superficie_alt"],
                              highlightthickness=0, bd=0, cursor="hand2")
        self.tela.pack(fill="x", pady=(5, 0))
        self.tela.bind("<Configure>", lambda e: self._desenhar())
        self.tela.bind("<Enter>", lambda e: self._mouse(True))
        self.tela.bind("<Leave>", lambda e: self._mouse(False))
        self.tela.bind("<Button-1>", lambda e: self.escolher())
        self.remover_link = tk.Label(self, text="Remover arquivo", bg=pai.cget("bg"),
                                     fg=T["perigo"], font=T.fonte(9), cursor="hand2")
        self.remover_link.bind("<Button-1>", lambda e: self.limpar())

    def _mouse(self, dentro):
        self._hover = dentro
        self._desenhar()

    def _desenhar(self):
        t = self.tela
        t.delete("all")
        largura = max(t.winfo_width(), 240)
        altura = self.ALTURA
        if self._hover:
            t.configure(bg=T["primaria_suave"])
        else:
            t.configure(bg=T["superficie_alt"])
        cor = T["sucesso"] if self.caminho else (T["primaria"] if self._hover else T["campo_borda"])
        t.create_rectangle(3, 3, largura - 3, altura - 3, outline=cor, dash=(5, 4), width=2)
        if not self.caminho:
            t.create_text(largura / 2, altura / 2 - 11, text="Clique para escolher o arquivo",
                          fill=T["texto"], font=T.fonte(10, "bold"))
            t.create_text(largura / 2, altura / 2 + 12,
                          text="PDF, PNG, JPG, DOC ou DOCX  ·  até 5 MB",
                          fill=T["suave"], font=T.fonte(9))
        else:
            try:
                tamanho = formatar_tamanho(os.path.getsize(self.caminho))
            except OSError:
                tamanho = ""
            t.create_text(largura / 2, altura / 2 - 11,
                          text="✓  " + abreviar(os.path.basename(self.caminho), 48),
                          fill=T["sucesso"], font=T.fonte(10, "bold"))
            t.create_text(largura / 2, altura / 2 + 12,
                          text=(tamanho + "  ·  " if tamanho else "") + "clique para trocar",
                          fill=T["suave"], font=T.fonte(9))

    def escolher(self):
        caminho = escolher_arquivo(self)
        if caminho:
            self.caminho = caminho
            self.remover_link.pack(anchor="e", pady=(4, 0))
            self._desenhar()
            if self._ao_mudar:
                self._ao_mudar()

    def limpar(self):
        self.caminho = ""
        self.remover_link.pack_forget()
        self._desenhar()
        if self._ao_mudar:
            self._ao_mudar()

    def valor(self):
        return self.caminho


# ------------------------------------------------------------------------ tabela
class Tabela(tk.Frame):
    """Lista com listras, rolagem fina, mensagem de lista vazia e seleção."""

    def __init__(self, pai, colunas, ao_abrir=None, ao_selecionar=None,
                 texto_vazio="Nada por aqui ainda."):
        """colunas = [(id, título, largura, âncora)]"""
        super().__init__(pai, bg=T["superficie"])
        self._ao_selecionar = ao_selecionar
        ids = [c[0] for c in colunas]
        self.arvore = ttk.Treeview(self, columns=ids, show="headings",
                                   selectmode="browse", style="Moderno.Treeview")
        for ident, titulo, largura, ancora in colunas:
            self.arvore.heading(ident, text=titulo.upper(), anchor=ancora)
            self.arvore.column(ident, width=largura, minwidth=50, anchor=ancora,
                               stretch=True)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.arvore.yview,
                              style="Moderno.Vertical.TScrollbar")
        self.arvore.configure(yscrollcommand=barra.set)
        self.arvore.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.arvore.tag_configure("par", background=T["superficie"])
        self.arvore.tag_configure("impar", background=T["zebra"])
        for tag, cor in (("ok", "sucesso"), ("erro", "perigo"),
                         ("aviso", "alerta"), ("info", "info")):
            self.arvore.tag_configure(tag, foreground=T[cor])

        self._vazio = tk.Label(self, text=texto_vazio, bg=T["superficie"],
                               fg=T["suave"], font=T.fonte(11))
        self.arvore.bind("<<TreeviewSelect>>", self._mudou_selecao)
        if ao_abrir:
            self.arvore.bind("<Double-1>", lambda e: self._duplo_clique(e, ao_abrir))
            self.arvore.bind("<Return>", lambda e: ao_abrir())

    def _duplo_clique(self, evento, ao_abrir):
        if self.arvore.identify_row(evento.y):
            ao_abrir()

    def _mudou_selecao(self, _):
        if self._ao_selecionar:
            self._ao_selecionar(self.selecionado())

    def preencher(self, linhas):
        """linhas = [(iid, valores, tag_extra ou None)]. Mantém a seleção."""
        anterior = self.selecionado()
        self.arvore.delete(*self.arvore.get_children())
        for posicao, (iid, valores, tag) in enumerate(linhas):
            tags = ("par" if posicao % 2 == 0 else "impar",)
            if tag:
                tags += (tag,)
            self.arvore.insert("", "end", iid=iid, values=valores, tags=tags)
        if anterior is not None and self.arvore.exists(anterior):
            self.arvore.selection_set(anterior)
        if linhas:
            self._vazio.place_forget()
        else:
            self._vazio.place(relx=0.5, rely=0.55, anchor="center")
        self._mudou_selecao(None)

    def definir_texto_vazio(self, texto):
        self._vazio.configure(text=texto)

    def selecionado(self):
        selecao = self.arvore.selection()
        return selecao[0] if selecao else None


# -------------------------------------------------------------------- notificações
class Notificador:
    """Avisos que deslizam no canto inferior direito e somem sozinhos."""
    TITULOS = {"sucesso": "Tudo certo", "erro": "Atenção", "aviso": "Aviso", "info": "Informação"}

    def __init__(self, raiz):
        self.raiz = raiz
        self._quadro = None
        self._agendado = None

    def mostrar(self, mensagem, tipo="sucesso", duracao=3600):
        self.esconder()
        forte, _ = cores_do_tipo(tipo)
        quadro = tk.Frame(self.raiz, bg=T["superficie"], highlightthickness=1,
                          highlightbackground=T["borda"], cursor="hand2")
        tk.Frame(quadro, bg=forte, width=5).pack(side="left", fill="y")
        corpo = tk.Frame(quadro, bg=T["superficie"])
        corpo.pack(side="left", padx=16, pady=12)
        tk.Label(corpo, text=self.TITULOS.get(tipo, ""), bg=T["superficie"], fg=forte,
                 font=T.fonte(10, "bold"), anchor="w").pack(anchor="w")
        tk.Label(corpo, text=mensagem, bg=T["superficie"], fg=T["texto"],
                 font=T.fonte(10), wraplength=340, justify="left",
                 anchor="w").pack(anchor="w", pady=(2, 0))
        for peca in (quadro, corpo, *corpo.winfo_children()):
            peca.bind("<Button-1>", lambda e: self.esconder())
        self._quadro = quadro
        self._deslizar(quadro, 0, entrando=True)
        self._agendado = self.raiz.after(duracao, self.esconder)

    def _deslizar(self, quadro, passo, entrando):
        total = 8
        if not quadro.winfo_exists():
            return
        progresso = passo / total
        suave = 1 - (1 - progresso) ** 3          # desaceleração
        deslocamento = (1 - suave) * 70 if entrando else suave * 70
        quadro.place(relx=1.0, rely=1.0, x=-28, y=-28 + int(deslocamento), anchor="se")
        quadro.lift()
        if passo < total:
            self.raiz.after(14, lambda: self._deslizar(quadro, passo + 1, entrando))
        elif not entrando:
            quadro.destroy()

    def esconder(self):
        if self._agendado is not None:
            try:
                self.raiz.after_cancel(self._agendado)
            except tk.TclError:
                pass
            self._agendado = None
        quadro, self._quadro = self._quadro, None
        if quadro is not None and quadro.winfo_exists():
            quadro.destroy()


# ----------------------------------------------------------------------- diálogos
class Dialogo(tk.Toplevel):
    """Janela modal com título, corpo, área de erro e rodapé de botões."""

    def __init__(self, raiz, titulo, largura=520, subtitulo=""):
        super().__init__(raiz)
        self.raiz = raiz
        self.withdraw()
        self.title(titulo)
        self.configure(bg=T["superficie"])
        self.resizable(False, False)
        self.transient(raiz)
        tk.Frame(self, width=largura, height=1, bg=T["superficie"]).pack()

        cabecalho = tk.Frame(self, bg=T["superficie"])
        cabecalho.pack(fill="x", padx=28, pady=(24, 16))
        tk.Label(cabecalho, text=titulo, bg=T["superficie"], fg=T["texto"],
                 font=T.fonte(16, "bold"), anchor="w").pack(fill="x")
        if subtitulo:
            tk.Label(cabecalho, text=subtitulo, bg=T["superficie"], fg=T["suave"],
                     font=T.fonte(10), anchor="w", justify="left",
                     wraplength=largura - 60).pack(fill="x", pady=(4, 0))

        self.corpo = tk.Frame(self, bg=T["superficie"])
        self.corpo.pack(fill="both", expand=True, padx=28)

        self._largura = largura
        self.rotulo_erro = tk.Label(
            self, bg=T["perigo_fundo"], fg=T["perigo"], font=T.fonte(10),
            anchor="w", justify="left", wraplength=largura - 90, padx=12, pady=8,
        )
        self.rodape = tk.Frame(self, bg=T["superficie"])
        self.rodape.pack(fill="x", padx=28, pady=(14, 24))
        self.bind("<Escape>", lambda e: self.destroy())

    def mostrar_erro(self, mensagem):
        self.rotulo_erro.configure(text=mensagem)
        self.rotulo_erro.pack(fill="x", padx=28, pady=(6, 0), before=self.rodape)

    def limpar_erro(self):
        self.rotulo_erro.pack_forget()

    def ao_apertar_enter(self, funcao):
        self.bind("<Return>", lambda e: funcao())

    def botoes(self, texto_principal, comando_principal, variante="primario",
               texto_cancelar="Cancelar"):
        """Botão principal à direita, cancelar ao lado."""
        Botao(self.rodape, texto_principal, comando_principal, variante).pack(side="right")
        if texto_cancelar:
            Botao(self.rodape, texto_cancelar, self.destroy, "secundario").pack(
                side="right", padx=(0, 10))

    def exibir(self):
        self.update_idletasks()
        largura, altura = self.winfo_reqwidth(), self.winfo_reqheight()
        x = self.raiz.winfo_rootx() + (self.raiz.winfo_width() - largura) // 2
        y = self.raiz.winfo_rooty() + max(20, (self.raiz.winfo_height() - altura) // 2)
        self.geometry("+" + str(max(0, x)) + "+" + str(max(0, y)))
        self.deiconify()
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_set()


def confirmar(raiz, titulo, mensagem, texto_ok="Confirmar", perigo=False):
    """Pergunta sim/não no estilo do sistema. Devolve True se confirmou."""
    resposta = {"ok": False}

    def aceitar():
        resposta["ok"] = True
        dialogo.destroy()

    dialogo = Dialogo(raiz, titulo, largura=440)
    tk.Label(dialogo.corpo, text=mensagem, bg=T["superficie"], fg=T["texto"],
             font=T.fonte(10), wraplength=390, justify="left",
             anchor="w").pack(fill="x")
    dialogo.botoes(texto_ok, aceitar, "perigo" if perigo else "primario")
    dialogo.exibir()
    raiz.wait_window(dialogo)
    if isinstance(raiz, Dialogo) and raiz.winfo_exists():
        try:
            raiz.grab_set()          # devolve o foco modal ao diálogo de baixo
        except tk.TclError:
            pass
    return resposta["ok"]


def rotulo_valor(pai, rotulo, valor, largura=200, cor=None):
    """Par 'RÓTULO pequeno / valor' usado nas telas de detalhes."""
    quadro = tk.Frame(pai, bg=pai.cget("bg"))
    tk.Label(quadro, text=rotulo.upper(), bg=pai.cget("bg"), fg=T["suave"],
             font=T.fonte(8, "bold"), anchor="w").pack(fill="x")
    tk.Label(quadro, text=valor or "—", bg=pai.cget("bg"), fg=cor or T["texto"],
             font=T.fonte(10), anchor="w", justify="left",
             wraplength=largura).pack(fill="x", pady=(2, 0))
    return quadro
