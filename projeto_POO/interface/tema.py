"""Cores, fontes e estilos do tema (claro e escuro)."""
import json
import os
from tkinter import ttk
from tkinter import font as tkfont

PALETAS = {
    "claro": {
        "fundo": "#F3F5FA", "superficie": "#FFFFFF", "superficie_alt": "#F6F7FC",
        "borda": "#E3E7F1", "texto": "#172033", "suave": "#667089",
        "primaria": "#4F46E5", "primaria_hover": "#4338CA", "primaria_press": "#3730A3",
        "primaria_suave": "#E8E7FD", "sobre_primaria": "#FFFFFF",
        "sidebar": "#111631", "sidebar_hover": "#1B2247", "sidebar_ativo": "#222B5C",
        "sidebar_texto": "#9AA3C7", "sidebar_destaque": "#818CF8",
        "sucesso": "#16A34A", "sucesso_fundo": "#DCFCE7",
        "perigo": "#DC2626", "perigo_fundo": "#FEE2E2",
        "alerta": "#D97706", "alerta_fundo": "#FEF3C7",
        "info": "#2563EB", "info_fundo": "#DBEAFE",
        "destaque": "#9333EA",
        "zebra": "#F9FAFD", "selecao": "#E3E4FC",
        "campo": "#FFFFFF", "campo_borda": "#D5DAE8",
    },
    "escuro": {
        "fundo": "#0E1224", "superficie": "#171C33", "superficie_alt": "#1E2441",
        "borda": "#2A3157", "texto": "#E8EBFA", "suave": "#8F98BD",
        "primaria": "#6366F1", "primaria_hover": "#7478F5", "primaria_press": "#575AE0",
        "primaria_suave": "#272C5C", "sobre_primaria": "#FFFFFF",
        "sidebar": "#0A0D1D", "sidebar_hover": "#141A36", "sidebar_ativo": "#1A2045",
        "sidebar_texto": "#8A93B8", "sidebar_destaque": "#818CF8",
        "sucesso": "#4ADE80", "sucesso_fundo": "#12301F",
        "perigo": "#F87171", "perigo_fundo": "#3A1717",
        "alerta": "#FBBF24", "alerta_fundo": "#3A2C0B",
        "info": "#60A5FA", "info_fundo": "#14264A",
        "destaque": "#C084FC",
        "zebra": "#1A2040", "selecao": "#2C3370",
        "campo": "#12172E", "campo_borda": "#2F3760",
    },
}

FAMILIAS_PREFERIDAS = (
    "Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter", "Ubuntu",
    "Noto Sans", "DejaVu Sans", "Arial",
)

PREFERENCIAS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preferencias.json"
)


class Tema:
    def __init__(self):
        self.nome = "claro"
        self.cores = dict(PALETAS["claro"])
        self.familia = "TkDefaultFont"

    def __getitem__(self, chave):
        return self.cores[chave]

    def definir(self, nome):
        if nome not in PALETAS:
            nome = "claro"
        self.nome = nome
        self.cores = dict(PALETAS[nome])

    def alternar(self):
        self.definir("escuro" if self.nome == "claro" else "claro")

    def fonte(self, tamanho=10, peso="normal"):
        return (self.familia, tamanho, peso)

    def detectar_fonte(self, raiz):
        disponiveis = set(tkfont.families(raiz))
        for familia in FAMILIAS_PREFERIDAS:
            if familia in disponiveis:
                self.familia = familia
                return
        self.familia = "TkDefaultFont"

    # -- preferência salva em disco
    def carregar(self):
        try:
            with open(PREFERENCIAS, encoding="utf-8") as f:
                self.definir(json.load(f).get("tema", "claro"))
        except (OSError, ValueError, AttributeError):
            self.definir("claro")

    def salvar(self):
        try:
            with open(PREFERENCIAS, "w", encoding="utf-8") as f:
                json.dump({"tema": self.nome}, f)
        except OSError:
            pass


T = Tema()


def aplicar_estilos(raiz):
    """Configura os widgets ttk (tabela, rolagem, combobox) com o tema atual."""
    estilo = ttk.Style(raiz)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")
    c = T.cores

    # --- tabela
    estilo.configure(
        "Moderno.Treeview", background=c["superficie"], fieldbackground=c["superficie"],
        foreground=c["texto"], rowheight=38, borderwidth=0, relief="flat",
        font=T.fonte(10),
    )
    # Tk 8.6.9 (Python 3.8/3.9 no Windows) ignora as cores das linhas se o mapa
    # padrão do Treeview não for filtrado; esta correção é inofensiva nas versões novas.
    def mapa_corrigido(opcao):
        padrao = estilo.map("Treeview", query_opt=opcao) or []
        return [item for item in padrao if item[:2] != ("!disabled", "!selected")]

    estilo.map(
        "Moderno.Treeview",
        background=[("selected", c["selecao"])] + mapa_corrigido("background"),
        foreground=[("selected", c["texto"])] + mapa_corrigido("foreground"),
    )
    estilo.layout("Moderno.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    estilo.configure(
        "Moderno.Treeview.Heading", background=c["superficie_alt"],
        foreground=c["suave"], relief="flat", borderwidth=0,
        font=T.fonte(9, "bold"), padding=(12, 10),
    )
    estilo.map("Moderno.Treeview.Heading", background=[("active", c["borda"])])

    # --- barra de rolagem fina, sem setas
    estilo.layout("Moderno.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {
            "sticky": "ns",
            "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],
        })
    ])
    estilo.configure(
        "Moderno.Vertical.TScrollbar", troughcolor=c["superficie"],
        background=c["borda"], bordercolor=c["superficie"],
        darkcolor=c["borda"], lightcolor=c["borda"], gripcount=0, width=10,
    )
    estilo.map(
        "Moderno.Vertical.TScrollbar",
        background=[("active", c["suave"]), ("pressed", c["suave"])],
    )

    # --- combobox
    estilo.configure(
        "Moderno.TCombobox", fieldbackground=c["campo"], background=c["campo"],
        foreground=c["texto"], bordercolor=c["campo_borda"],
        lightcolor=c["campo_borda"], darkcolor=c["campo_borda"],
        arrowcolor=c["suave"], padding=8, relief="flat",
        selectbackground=c["campo"], selectforeground=c["texto"],
    )
    estilo.map(
        "Moderno.TCombobox",
        fieldbackground=[("readonly", c["campo"]), ("disabled", c["superficie_alt"])],
        foreground=[("disabled", c["suave"])],
        selectbackground=[("readonly", c["campo"])],
        selectforeground=[("readonly", c["texto"])],
        bordercolor=[("focus", c["primaria"])],
        lightcolor=[("focus", c["primaria"])],
        darkcolor=[("focus", c["primaria"])],
        arrowcolor=[("hover", c["texto"])],
    )
    # lista suspensa do combobox (é um Listbox comum do Tk)
    raiz.option_add("*TCombobox*Listbox.background", c["superficie"])
    raiz.option_add("*TCombobox*Listbox.foreground", c["texto"])
    raiz.option_add("*TCombobox*Listbox.selectBackground", c["primaria"])
    raiz.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    raiz.option_add("*TCombobox*Listbox.font", T.fonte(10))
