# Infosiga Analytics

Sistema para análise de acidentes de trânsito a partir de planilhas exportadas do Infosiga.

## Tecnologias

- Python
- Django
- Pandas
- Bootstrap
- SQLite

## Como executar

### Clonar o projeto

```bash
git clone https://github.com/viniciusv-erpdev/Infosiga-Analytics
```

Entrar na pasta:

```bash
cd infosiga-analytics
```

Criar ambiente virtual:

```bash
python -m venv venv
```

Ativar ambiente:

CMD:

```cmd
venv\Scripts\activate
```

PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar migrações:

```bash
python manage.py migrate
```

Iniciar servidor:

```bash
python manage.py runserver
```

Abrir:

```text
http://127.0.0.1:8000/
```

## Estrutura do projeto

```text
dashboard/
templates/
static/
config/
```
