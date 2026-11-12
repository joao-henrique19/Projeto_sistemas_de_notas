"""Pequenas funções que dependem do sistema operacional."""
import os
import subprocess
import sys


def abrir_arquivo(caminho):
    """Abre o arquivo no programa padrão do sistema (leitor de PDF, imagens...)."""
    if sys.platform.startswith("win"):
        os.startfile(caminho)                       # noqa: só existe no Windows
    elif sys.platform == "darwin":
        subprocess.Popen(["open", caminho])
    else:
        subprocess.Popen(["xdg-open", caminho])
