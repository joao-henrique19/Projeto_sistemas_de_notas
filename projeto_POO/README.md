# Sistema Escolar (POO + interface gráfica)

## Como executar
Requer Python 3.8+ com tkinter (já incluído no Python do Windows/macOS;
no Linux: `sudo apt install python3-tk`). Não precisa instalar mais nada.

    python main.py

Arquivos criados automaticamente na pasta do projeto:
- `dados.json` – todos os dados (salvos a cada alteração)
- `documentos/` – documentos anexados às justificativas de falta
- `preferencias.json` – tema escolhido (claro/escuro)

## Testes da lógica
    python -m unittest discover -s testes -t .

## Novidades
- **Justificativas de falta**: envio de documento (PDF, PNG, JPG, DOC, DOCX, até 5 MB),
  motivo, horas e data da falta. Cada pedido nasce *Pendente* e pode ser
  *Deferido* ou *Indeferido* (com parecer obrigatório). Quando deferido, as horas
  são **abonadas** e a frequência do boletim é recalculada automaticamente.
- Painel inicial com números, situação dos boletins e alertas de frequência.
- Interface nova: barra lateral, modo claro/escuro, formulários em janelas,
  máscaras de CPF/telefone/CEP/data, prévia de média e frequência ao lançar notas,
  avisos animados.

## Estrutura
- `main.py` – ponto de entrada
- `escola.py` – classe `Escola`: regras de negócio, validações, documentos e salvamento (sem interface)
- `interface/` – `app.py` (janela), `tema.py`, `componentes.py`, `base.py` e uma `pagina_*.py` por tela
- `alunos/` – `Aluno` e geração de matrícula
- `academico/` – `Professor`, `Materia`, `Boletim`, `Justificativa`
- `validacoes/` e `formatacoes/` – validadores, formatadores, máscaras e gerador de e-mail
- `testes/` – testes automatizados

## Regras do boletim
Média das 3 notas (0 a 100). Aprovado com média ≥ 60 e frequência ≥ 75%.
Frequência = (carga horária − faltas + horas abonadas) / carga horária.
(constantes `MEDIA_MINIMA` e `FREQUENCIA_MINIMA` em `academico/boletim.py`)
