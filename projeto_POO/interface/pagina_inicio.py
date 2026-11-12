"""Painel inicial: números gerais, situação dos boletins e alertas."""
import tkinter as tk

from academico.boletim import MEDIA_MINIMA, FREQUENCIA_MINIMA
from academico.justificativa import STATUS_PENDENTE
from interface.base import Pagina
from interface.componentes import Botao, Cartao, selo
from interface.tema import T

LIMITE_ATENCAO = 85      # frequência (%) abaixo da qual o aluno entra em "atenção"
TIPO_STATUS = {"Pendente": "aviso", "Deferida": "sucesso", "Indeferida": "erro"}


class PaginaInicio(Pagina):
    titulo = "Visão geral"
    subtitulo = "Um resumo do que está acontecendo na escola."

    def __init__(self, pai, app):
        super().__init__(pai, app)
        self._valores = {}          # número exibido por cartão (para animar a mudança)
        self._numeros = {}
        self.conteudo.columnconfigure(0, weight=1)
        self.conteudo.rowconfigure(1, weight=1)

        # linha 1: cartões de números
        self.linha_numeros = tk.Frame(self.conteudo, bg=T["fundo"])
        self.linha_numeros.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        definicoes = [
            ("alunos", "Alunos", "primaria", "alunos"),
            ("professores", "Professores", "info", "professores"),
            ("materias", "Matérias", "destaque", "materias"),
            ("boletins", "Boletins lançados", "sucesso", "notas"),
            ("pendentes", "Justificativas pendentes", "alerta", "justificativas"),
        ]
        for posicao, (chave, rotulo, cor, destino) in enumerate(definicoes):
            self.linha_numeros.columnconfigure(posicao, weight=1, uniform="n")
            self._cartao_numero(posicao, chave, rotulo, cor, destino)

        # linha 2: três cartões
        self.linha_baixo = tk.Frame(self.conteudo, bg=T["fundo"])
        self.linha_baixo.grid(row=1, column=0, sticky="nsew")
        for coluna in range(3):
            self.linha_baixo.columnconfigure(coluna, weight=1, uniform="b")
        self.linha_baixo.rowconfigure(0, weight=1)

        self.cartao_situacao = Cartao(self.linha_baixo)
        self.cartao_situacao.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.cartao_atencao = Cartao(self.linha_baixo)
        self.cartao_atencao.grid(row=0, column=1, sticky="nsew", padx=9)
        self.cartao_recentes = Cartao(self.linha_baixo)
        self.cartao_recentes.grid(row=0, column=2, sticky="nsew", padx=(9, 0))

    # ----------------------------------------------------------- construção
    def _cartao_numero(self, posicao, chave, rotulo, cor, destino):
        cartao = Cartao(self.linha_numeros, pady=16)
        cartao.grid(row=0, column=posicao, sticky="ew", padx=(0 if posicao == 0 else 9, 0))
        tk.Frame(cartao.corpo, bg=T[cor], width=28, height=4).pack(anchor="w")
        numero = tk.Label(cartao.corpo, text="0", bg=T["superficie"], fg=T["texto"],
                          font=T.fonte(28, "bold"), anchor="w")
        numero.pack(anchor="w", pady=(8, 0))
        legenda = tk.Label(cartao.corpo, text=rotulo, bg=T["superficie"], fg=T["suave"],
                           font=T.fonte(10), anchor="w")
        legenda.pack(anchor="w")
        self._numeros[chave] = numero
        self._valores[chave] = 0
        for peca in (cartao, cartao.corpo, numero, legenda):
            peca.configure(cursor="hand2")
            peca.bind("<Button-1>", lambda e, d=destino: self.app.ir(d))

    @staticmethod
    def _titulo_cartao(cartao, titulo, subtitulo=""):
        tk.Label(cartao.corpo, text=titulo, bg=T["superficie"], fg=T["texto"],
                 font=T.fonte(12, "bold"), anchor="w").pack(fill="x")
        if subtitulo:
            tk.Label(cartao.corpo, text=subtitulo, bg=T["superficie"], fg=T["suave"],
                     font=T.fonte(9), anchor="w").pack(fill="x", pady=(2, 0))
        tk.Frame(cartao.corpo, bg=T["borda"], height=1).pack(fill="x", pady=(12, 10))

    @staticmethod
    def _limpar(cartao):
        for filho in cartao.corpo.winfo_children():
            filho.destroy()

    # ------------------------------------------------------------ animações
    def _animar_numero(self, chave, alvo):
        inicio = self._valores.get(chave, 0)
        self._valores[chave] = alvo
        rotulo = self._numeros[chave]
        passos = 14

        def passo(i):
            if not rotulo.winfo_exists():
                return
            valor = round(inicio + (alvo - inicio) * (1 - (1 - i / passos) ** 3))
            rotulo.configure(text=str(valor))
            if i < passos:
                rotulo.after(18, lambda: passo(i + 1))

        if inicio == alvo:
            rotulo.configure(text=str(alvo))
        else:
            passo(0)

    @staticmethod
    def _animar_barra(preenchimento, alvo):
        passos = 16

        def passo(i):
            if not preenchimento.winfo_exists():
                return
            fracao = alvo * (1 - (1 - i / passos) ** 3)
            preenchimento.place_configure(relwidth=max(fracao, 0.0001))
            if i < passos:
                preenchimento.after(16, lambda: passo(i + 1))

        passo(0)

    # ----------------------------------------------------------- atualização
    def atualizar(self):
        e = self.escola
        self._animar_numero("alunos", len(e.alunos))
        self._animar_numero("professores", len(e.professores))
        self._animar_numero("materias", len(e.materias))
        self._animar_numero("boletins", len(e.boletins))
        self._animar_numero("pendentes", e.contar_justificativas(STATUS_PENDENTE))
        self._desenhar_situacao()
        self._desenhar_atencao()
        self._desenhar_recentes()

    def _desenhar_situacao(self):
        cartao = self.cartao_situacao
        self._limpar(cartao)
        self._titulo_cartao(cartao, "Situação dos boletins", "Média ≥ " + str(MEDIA_MINIMA)
                            + " e frequência ≥ " + str(FREQUENCIA_MINIMA) + "%")
        boletins = self.escola.boletins
        if not boletins:
            tk.Label(cartao.corpo, text="Lance notas para ver o resumo aqui.",
                     bg=T["superficie"], fg=T["suave"], font=T.fonte(10)).pack(pady=24)
            return
        contagem = {"ok": 0, "nota": 0, "falta": 0, "ambos": 0}
        for b in boletins:
            por_nota = b.media < MEDIA_MINIMA
            por_falta = b.frequencia < FREQUENCIA_MINIMA
            if por_nota and por_falta:
                contagem["ambos"] += 1
            elif por_nota:
                contagem["nota"] += 1
            elif por_falta:
                contagem["falta"] += 1
            else:
                contagem["ok"] += 1
        total = len(boletins)
        for rotulo, chave, cor in (
            ("Aprovados", "ok", "sucesso"), ("Reprovados por nota", "nota", "perigo"),
            ("Reprovados por falta", "falta", "alerta"),
            ("Reprovados por nota e falta", "ambos", "destaque"),
        ):
            linha = tk.Frame(cartao.corpo, bg=T["superficie"])
            linha.pack(fill="x", pady=(0, 12))
            topo = tk.Frame(linha, bg=T["superficie"])
            topo.pack(fill="x")
            tk.Label(topo, text=rotulo, bg=T["superficie"], fg=T["texto"],
                     font=T.fonte(10)).pack(side="left")
            tk.Label(topo, text=str(contagem[chave]) + "  (" + format(
                contagem[chave] / total * 100, ".0f") + "%)", bg=T["superficie"],
                fg=T["suave"], font=T.fonte(10)).pack(side="right")
            trilho = tk.Frame(linha, bg=T["borda"], height=8)
            trilho.pack(fill="x", pady=(6, 0))
            trilho.pack_propagate(False)
            preenchimento = tk.Frame(trilho, bg=T[cor])
            preenchimento.place(relx=0, rely=0, relheight=1, relwidth=0.0001)
            self._animar_barra(preenchimento, contagem[chave] / total)

    def _desenhar_atencao(self):
        cartao = self.cartao_atencao
        self._limpar(cartao)
        self._titulo_cartao(cartao, "Frequência em atenção",
                            "Abaixo de " + str(LIMITE_ATENCAO) + "% (mínimo " + str(FREQUENCIA_MINIMA) + "%)")
        risco = sorted((b for b in self.escola.boletins if b.frequencia < LIMITE_ATENCAO),
                       key=lambda b: b.frequencia)
        if not risco:
            tk.Label(cartao.corpo, text="Tudo em dia: nenhum aluno com\nfrequência baixa.",
                     bg=T["superficie"], fg=T["suave"], font=T.fonte(10),
                     justify="center").pack(pady=24)
            return
        for b in risco[:6]:
            linha = tk.Frame(cartao.corpo, bg=T["superficie"])
            linha.pack(fill="x", pady=4)
            textos = tk.Frame(linha, bg=T["superficie"])
            textos.pack(side="left", fill="x", expand=True)
            tk.Label(textos, text=b.aluno.nome, bg=T["superficie"], fg=T["texto"],
                     font=T.fonte(10, "bold"), anchor="w").pack(fill="x")
            tk.Label(textos, text=b.materia.nome + "  ·  " + str(b.faltas_efetivas) + " h de falta",
                     bg=T["superficie"], fg=T["suave"], font=T.fonte(9), anchor="w").pack(fill="x")
            critico = b.frequencia < FREQUENCIA_MINIMA
            selo(linha, format(b.frequencia, ".0f") + "%", "erro" if critico else "aviso").pack(side="right")
        if len(risco) > 6:
            tk.Label(cartao.corpo, text="+ " + str(len(risco) - 6) + " outros", bg=T["superficie"],
                     fg=T["suave"], font=T.fonte(9)).pack(anchor="w", pady=(6, 0))

    def _desenhar_recentes(self):
        cartao = self.cartao_recentes
        self._limpar(cartao)
        self._titulo_cartao(cartao, "Justificativas recentes", "Últimos pedidos de abono de falta")
        recentes = self.escola.justificativas[-6:][::-1]
        if not recentes:
            tk.Label(cartao.corpo, text="Nenhuma justificativa enviada.", bg=T["superficie"],
                     fg=T["suave"], font=T.fonte(10)).pack(pady=(24, 12))
        for j in recentes:
            linha = tk.Frame(cartao.corpo, bg=T["superficie"])
            linha.pack(fill="x", pady=4)
            textos = tk.Frame(linha, bg=T["superficie"])
            textos.pack(side="left", fill="x", expand=True)
            tk.Label(textos, text=j.aluno.nome, bg=T["superficie"], fg=T["texto"],
                     font=T.fonte(10, "bold"), anchor="w").pack(fill="x")
            tk.Label(textos, text=j.materia.nome + "  ·  " + j.data_falta + "  ·  " + str(j.horas) + " h",
                     bg=T["superficie"], fg=T["suave"], font=T.fonte(9), anchor="w").pack(fill="x")
            selo(linha, j.status, TIPO_STATUS[j.status]).pack(side="right")
        Botao(cartao.corpo, "Ver todas", lambda: self.app.ir("justificativas"),
              "fantasma", altura=32, tamanho=9).pack(anchor="w", pady=(8, 0))
