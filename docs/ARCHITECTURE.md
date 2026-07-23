# Infosiga Analytics - Arquitetura

## Objetivo

O Infosiga Analytics é um sistema web desenvolvido em Django para realizar análises sobre acidentes de trânsito disponibilizados pelo Infosiga SP.

O sistema tem como objetivo transformar planilhas CSV/XLSX em informações consolidadas através de filtros, pré-processamento, regularização de logradouros e futuramente dashboards e mapas.

---

# Tecnologias

- Python 3
- Django
- Pandas
- RapidFuzz
- Bootstrap 5
- SQLite

---

# Estrutura do projeto

```
infosiga-analytics/

analytics/
│
├── forms.py
├── views.py
│
├── services/
│   │
│   ├── file_loader.py
│   ├── filters.py
│   │
│   └── preprocessing/
│       ├── pipeline.py
│       ├── address_normalizer.py
│       ├── address_cluster.py
│       ├── address_matcher.py
│       ├── similarity.py
│       └── address_dictionary.py
│
├── templates/
│
├── static/
│
└── models.py
```

---

# Responsabilidades

## views.py

Responsável apenas por:

- receber requisições
- chamar os serviços
- montar o contexto
- renderizar templates

Nunca deve conter regras de negócio.

---

## file_loader.py

Responsável por:

- validar upload
- ler CSV/XLSX
- aplicar filtros
- executar pipeline
- preparar preview
- armazenar informações na Session

Não deve conter lógica de normalização.

---

## filters.py

Responsável pelos filtros de negócio.

Exemplo:

- município
- tipo de via
- tipo de registro

---

## preprocessing/

Toda transformação dos dados ocorre aqui.

Cada módulo possui uma única responsabilidade.

---

### address_normalizer.py

Normalização textual.

Exemplos:

```
Av.
→ avenida

São
→ sao

-
→ espaço
```

Não realiza comparações.

---

### similarity.py

Encapsula todas as funções do RapidFuzz.

Nenhum outro módulo deve utilizar RapidFuzz diretamente.

---

### address_cluster.py

Agrupa logradouros semelhantes.

Não altera DataFrames.

Recebe listas.

Retorna clusters.

---

### address_dictionary.py

Constrói o dicionário

logradouro normalizado

↓

logradouro canônico

---

### address_matcher.py

Aplica o dicionário ao DataFrame.

Cria colunas como

- logradouro_canonico
- similaridade
- frequencia_grupo

---

### pipeline.py

Coordena todas as etapas do pré-processamento.

Fluxo atual:

```
normalize()

↓

cluster()

↓

dictionary()

↓

matcher()
```

Novas etapas deverão ser adicionadas aqui.

---

# Templates

Utilizar Django Template Tags.

Evitar duplicação.

Sempre utilizar:

```
base.html
```

como template principal.

---

# Front-end

Bootstrap 5

Sem React

Sem TypeScript

Sem Vue

Utilizar apenas:

- Django Templates
- HTML
- CSS
- JavaScript puro

---

# Princípios

- Código simples
- Alta coesão
- Baixo acoplamento
- Cada módulo possui uma responsabilidade
- Views finas
- Serviços reutilizáveis