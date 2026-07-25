# Projeto: Infosiga Analytics

## Objetivo

O Infosiga Analytics é um sistema web desenvolvido para análise de acidentes de trânsito a partir das bases de dados públicas do Infosiga/Detran.

O objetivo principal é permitir que usuários importem planilhas CSV ou XLSX, filtrem os dados e visualizem estatísticas sobre acidentes, atropelamentos e padrões viários.

O sistema deve ser simples, modular e fácil de expandir.

---

# Tecnologias

- Python
- Django
- Pandas
- Bootstrap 5
- SQLite

---

# Estrutura do projeto

- Pasta raiz: `infosiga-analytics`
- Aplicação principal: `analytics`

Estrutura relevante:

```text
analytics/

├── forms.py
├── views.py
├── urls.py
├── models.py
│
├── services/
│   ├── file_loader.py
│   ├── filters.py
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── address_normalizer.py
│   │   ├── address_matcher.py
│   │   └── address_dictionary.py
│
├── templates/
├── static/
```

---

# Fluxo arquitetural obrigatório

Toda nova funcionalidade deve respeitar a seguinte arquitetura:

```text
views.py

↓

services/file_loader.py

↓

services/filters.py

↓

services/preprocessing/pipeline.py

↓

templates
```

IMPORTANTE:

- A view NÃO deve implementar regras de negócio.
- A view NÃO deve manipular DataFrames diretamente.
- A view NÃO deve executar filtros.
- A view NÃO deve normalizar dados.
- A view NÃO deve construir lógica de preprocessing.

A view deve apenas:

- receber a requisição;
- chamar os serviços;
- montar o contexto;
- renderizar o template.

---

# Responsabilidades

## views.py

Responsável apenas por:

- receber requisições;
- chamar serviços;
- renderizar páginas;
- enviar dados ao template.

Não deve:

- carregar DataFrames;
- aplicar filtros;
- normalizar logradouros;
- criar métricas.

---

## file_loader.py

Responsável por:

- validar arquivos;
- ler CSV/XLSX;
- criar DataFrames;
- orquestrar o pipeline de processamento;
- salvar informações necessárias na sessão.

Não deve conter lógica de interface.

---

## filters.py

Responsável por:

- filtrar município;
- filtrar tipo de via;
- filtrar tipo de sinistro.

Filtros atuais:

- município = Ribeirão Preto;
- tipo_via = VIAS URBANAS ou ESTRADAS E RODOVIAS;
- tipo_registro = SINISTRO FATAL ou SINISTRO NAO FATAL;
- nunca incluir registros NOTIFICACAO.

---

## preprocessing/pipeline.py

Responsável por executar todas as etapas de pré-processamento.

Exemplo:

```python
df = run_preprocessing(df)
```

A view não deve conhecer as etapas internas do pipeline.

---

## preprocessing/address_normalizer.py

Responsável por:

- converter para minúsculas;
- remover acentos;
- remover espaços duplicados;
- padronizar abreviações;
- criar a coluna `logradouro_normalizado`.

Nunca modificar a coluna original `logradouro`.

Exemplo:

```text
Av. Independência
→ avenida independencia

Rod. Anhanguera
→ rodovia anhanguera
```

---

## preprocessing/address_matcher.py

Futuro módulo responsável por:

- utilizar RapidFuzz;
- encontrar logradouros semelhantes;
- calcular scores de similaridade;
- sugerir agrupamentos.

Ainda não implementado.

---

## preprocessing/address_dictionary.py

Futuro módulo responsável por:

- armazenar logradouros padronizados;
- definir rótulos canônicos;
- servir como dicionário mestre.

Ainda não implementado.

---

# Estratégia para categorização de logradouros

O sistema utilizará três etapas:

## Etapa 1 — Normalização

Transformar:

```text
Av Independência
AV. Independência
Avenida Independencia
```

em:

```text
avenida independencia
```

---

## Etapa 2 — Agrupamento

Agrupar logradouros semelhantes utilizando:

- frequência;
- regras determinísticas;
- RapidFuzz.

---

## Etapa 3 — Rótulo canônico

Escolher um único nome oficial para cada grupo.

Exemplo:

```text
Avenida Independência
```

---

# Diretrizes de desenvolvimento

- Utilizar Django Templates.
- Utilizar Bootstrap 5.
- Não usar React.
- Não usar TypeScript.
- Não duplicar lógica.
- Não carregar o mesmo DataFrame duas vezes.
- Não espalhar responsabilidades entre view e services.
- Manter o código simples e modular.
- Explicar alterações arquiteturais antes de gerar código.

---

# Banco de validação de logradouros

O projeto possui uma camada de persistência responsável por armazenar correções manuais e validações definitivas de logradouros.

Esse banco funciona como uma fonte de verdade para o pipeline de preprocessing.

Fluxo:

Dados Infosiga

↓

Normalização automática

↓

Consulta ao banco AddressCorrection

↓

Aplicação das correções aprovadas

↓

Dados finais para análise


---

# Modelo AddressCorrection

Localização:

analytics/models.py


Responsabilidade:

Armazenar relacionamentos entre logradouros encontrados nos dados e seus respectivos nomes canônicos.


Campos principais:

- logradouro_original:
    valor encontrado originalmente no dataset.

- logradouro_limpo:
    valor normalizado utilizado para comparação.

- logradouro_canonico:
    nome oficial definido pelo usuário ou algoritmo.

- corrigido_manualmente:
    indica se houve validação humana.

- autor:
    usuário responsável pela alteração.

- created_at:
    data de criação.

- updated_at:
    última atualização.


---

# Camada de persistência de correções

Localização:

analytics/persistence/corrections.py


Responsabilidade:

Centralizar acesso ao banco de correções.


O pipeline nunca deve acessar diretamente:

AddressCorrection.objects.filter()


Toda consulta ao banco deve passar por funções de serviço.


Exemplo:

```python
correction = get_correction_by_limpo(
    logradouro_normalizado
)