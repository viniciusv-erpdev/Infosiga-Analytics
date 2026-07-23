# COPILOT GUIDELINES

# Projeto

Nome: Infosiga Analytics

Objetivo:

Sistema web desenvolvido em Django para análise de acidentes de trânsito do Infosiga-SP.

O projeto deve priorizar simplicidade, organização, modularidade e facilidade de manutenção.

---

# Tecnologias

Utilizar apenas:

- Python
- Django
- Pandas
- RapidFuzz
- Bootstrap 5
- SQLite

Não utilizar:

- React
- Vue
- Angular
- TypeScript
- APIs externas para processamento de dados
- JavaScript desnecessário

---

# Arquitetura

O projeto segue arquitetura baseada em serviços.

As Views NÃO implementam regras de negócio.

Fluxo esperado:

View

↓

Service

↓

Preprocessing

↓

Resultado

Toda regra de negócio deve permanecer dentro da pasta:

analytics/services/

---

# Responsabilidade dos módulos

## views.py

Responsável apenas por:

- receber requisições
- chamar serviços
- montar contexto
- renderizar templates
- retornar respostas HTTP

Nunca implementar:

- filtros
- processamento
- normalização
- RapidFuzz
- Pandas

---

## file_loader.py

Responsável por:

- validar uploads
- ler CSV/XLSX
- aplicar filtros
- executar pipeline
- gerar preview
- armazenar dados na Session

---

## filters.py

Responsável exclusivamente pelos filtros de negócio.

Exemplos:

- município
- tipo de via
- tipo de registro

Não realizar processamento textual.

---

## preprocessing/

Toda transformação dos dados ocorre aqui.

Cada arquivo possui uma responsabilidade única.

---

### address_normalizer.py

Responsável por normalizar textos.

Pode:

- remover acentos
- remover pontuação
- padronizar abreviações
- lowercase
- remover espaços duplicados

Não pode:

- usar RapidFuzz
- comparar strings
- acessar DataFrames completos

---

### similarity.py

Único módulo autorizado a utilizar RapidFuzz.

Qualquer comparação de similaridade deve passar por este módulo.

Não chamar RapidFuzz diretamente em outros arquivos.

---

### address_cluster.py

Responsável apenas por agrupar logradouros semelhantes.

Recebe listas.

Retorna clusters.

Não altera DataFrames.

---

### address_dictionary.py

Responsável por construir o dicionário:

logradouro_normalizado

↓

logradouro_canônico

---

### address_matcher.py

Responsável por aplicar o dicionário ao DataFrame.

Cria colunas como:

- logradouro_canonico
- similaridade
- frequencia_grupo

Não deve realizar clustering.

---

### pipeline.py

Responsável por coordenar todo o pré-processamento.

Fluxo atual:

normalize

↓

cluster

↓

dictionary

↓

matcher

Novas etapas deverão ser adicionadas aqui.

---

# Dados

Nunca alterar os dados originais.

Sempre criar novas colunas.

Exemplo:

logradouro

↓

logradouro_normalizado

↓

logradouro_canonico

---

# Interface

Sempre utilizar:

Django Template Tags

Estrutura:

base.html

↓

templates específicos

Evitar duplicação de HTML.

Sempre reutilizar componentes.

---

# Bootstrap

Utilizar Bootstrap 5.

Evitar CSS excessivamente complexo.

Priorizar:

- Cards
- Grid
- Containers
- Utilitários Bootstrap

---

# JavaScript

Utilizar JavaScript puro.

Não adicionar bibliotecas apenas para pequenas funcionalidades.

Todo JS deve ser desacoplado do backend.

---

# Organização

Cada módulo deve possuir apenas uma responsabilidade.

Evitar funções muito grandes.

Preferir funções pequenas e reutilizáveis.

---

# Código

Priorizar:

- legibilidade
- simplicidade
- baixo acoplamento
- alta coesão

Não escrever código "esperto".

Escrever código fácil de manter.

---

# Performance

Evitar:

- loops desnecessários
- múltiplas leituras do DataFrame
- processamento repetido
- recalcular dados já existentes

Sempre reutilizar resultados intermediários.

---

# Testes

Sempre que uma alteração modificar uma regra de negócio importante, sugerir testes unitários.

Os testes devem utilizar:

- Django TestCase
- unittest.mock
- DataFrames pequenos

---

# Roadmap

O desenvolvimento deve seguir esta ordem:

1. Arquitetura
2. Upload
3. Filtros
4. Pipeline
5. Normalização
6. Agrupamento
7. Regularização
8. Dashboard
9. Heatmap
10. Estatísticas
11. Exportação

Evitar implementar funcionalidades futuras antes da conclusão da etapa atual.

---

# Durante sugestões de código

Sempre verificar:

✓ A lógica pertence realmente a este módulo?

✓ Existe algum serviço que já faz isso?

✓ A responsabilidade está correta?

✓ É possível reutilizar código existente?

✓ Existe duplicação?

Se alguma resposta for "sim", reutilizar a implementação existente ao invés de criar uma nova.

---

# Objetivo final

O Infosiga Analytics deverá se tornar uma plataforma completa para análise de acidentes de trânsito.

Além da visualização dos dados, o sistema deverá ser capaz de:

- corrigir automaticamente logradouros inconsistentes;
- agrupar vias semelhantes;
- gerar estatísticas;
- produzir dashboards;
- gerar mapas de calor;
- servir como ferramenta de apoio para pesquisa e tomada de decisão.

Toda implementação deve preservar a arquitetura modular do projeto e facilitar futuras expansões.