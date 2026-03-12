# Sistema de Triagem Hospitalar (TCC)

Aplicacao web para apoio a triagem hospitalar com:

- Cadastro de paciente
- Coleta de sinais vitais e sintomas
- Predicao de prioridade ESI (1 a 5) com modelo de machine learning
- Regras de seguranca para reduzir subtriagem em casos criticos
- Persistencia em SQLite

## Aviso importante

Este projeto e um sistema de apoio a decisao e NAO substitui avaliacao clinica profissional.

## Tecnologias

- Python 3.14
- Flask
- scikit-learn
- pandas
- joblib
- SQLite

## Estrutura do projeto

```text
triagem-hospitalar-tcc/
|-- app.py
|-- conexao.py
|-- preparar_dados.py
|-- treinar_modelo.py
|-- modelo.pkl
|-- model_metadata.json
|-- triagem.db
|-- data/
|   `-- dataset_limpo.csv
|-- templates/
|   |-- Cadastro.html
|   |-- Sintomas.html
|   `-- Resultado.html
`-- Static/
		|-- Style.css
		`-- Script.js
```

## Como executar

### Opcao 1: Prompt de Comando (cmd)

```bat
cd C:\Users\Leo\Desktop\triagem-hospitalar-tcc
.\.venv\Scripts\activate.bat
python app.py
```

### Opcao 2: PowerShell

```powershell
Set-Location C:\Users\Leo\Desktop\triagem-hospitalar-tcc
& .\.venv\Scripts\Activate.ps1
python app.py
```

Depois abra no navegador:

- http://127.0.0.1:5000

## Instalacao de dependencias

Se o ambiente virtual nao existir:

```powershell
py -3 -m venv .venv
```

Instale as bibliotecas principais:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install flask joblib pandas scikit-learn pyreadr
```

## Banco de dados

O banco SQLite e inicializado automaticamente ao iniciar o app.

- Arquivo: `triagem.db`
- Tabelas principais:
	- `pacientes`
	- `triagens`
	- `sintomas`
	- `triagem_sintomas`

## Fluxo de dados e modelo

### 1. Preparacao de dados

Script: `preparar_dados.py`

Entrada esperada:

- `5v_cleandf.rdata`

Saida:

- `data/dataset_limpo.csv`

### 2. Treinamento

Script: `treinar_modelo.py`

Saidas:

- `modelo.pkl`
- `model_metadata.json`

O treinamento atual inclui:

- balanceamento de classes
- pesos maiores para classes graves (ESI 4 e 5)
- calibracao de probabilidades
- metricas extras para deteccao de alto risco

### 3. Inferencia no app

Script: `app.py`

- monta vetor de entrada com as features do modelo
- executa predicao de ESI
- aplica regra de seguranca clinica (override) para cenarios criticos
- salva resultado no banco

## Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'joblib'`

Voce esta fora da venv ou sem dependencia instalada.

```powershell
& .\.venv\Scripts\Activate.ps1
python -m pip install joblib
```

### Erro no cmd: `& foi inesperado neste momento`

No cmd, use `activate.bat` (nao `Activate.ps1`).

```bat
.\.venv\Scripts\activate.bat
```

### App rodando com Streamlit por engano

Este projeto usa Flask. Execute:

```powershell
python app.py
```

e nao:

```powershell
streamlit run app.py
```

## Melhorias futuras

- dashboard de auditoria de triagens
- explicabilidade de predicao (feature importance por atendimento)
- validacao externa com base hospitalar real
- autentificacao e perfis de usuario

## Licenca

Definir licenca do projeto (ex.: MIT) conforme orientacao do TCC.