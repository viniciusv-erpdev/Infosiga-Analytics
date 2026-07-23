# Pipeline de Pré-processamento

## Objetivo

Padronizar logradouros mantendo sempre o valor original.

Nunca alterar a coluna original.

---

# Fluxo

```
CSV

↓

Pandas

↓

Filtros

↓

Normalização

↓

Agrupamento

↓

Regularização

↓

Preview

↓

Dashboard
```

---

# Etapa 1

Leitura

Responsável:

```
file_loader.py
```

Resultado:

DataFrame bruto.

---

# Etapa 2

Filtros

Responsável:

```
filters.py
```

Filtros atuais

- Município
- Tipo de Via
- Tipo de Registro

---

# Etapa 3

Normalização

Responsável:

```
address_normalizer.py
```

Transformações:

- lowercase
- remover acentos
- remover pontuação
- padronizar abreviações
- remover espaços duplicados

Resultado:

```
logradouro_normalizado
```

---

# Etapa 4

Clustering

Responsável

```
address_cluster.py
```

Objetivo

Agrupar logradouros semelhantes.

Exemplo

```
Av Independência

↓

Avenida Independencia

↓

avenida independencia
```

---

# Etapa 5

Similaridade

Responsável

```
similarity.py
```

RapidFuzz

token_sort_ratio()

---

# Etapa 6

Construção do dicionário

Responsável

```
address_dictionary.py
```

Exemplo

```
avenida independencia

↓

avenida independência
```

---

# Etapa 7

Regularização

Responsável

```
address_matcher.py
```

Criação das colunas

- logradouro_canonico
- similaridade
- frequencia_grupo

---

# Colunas atuais

Original

```
logradouro
```

Normalizado

```
logradouro_normalizado
```

Canônico

```
logradouro_canonico
```

Score

```
similaridade
```

Frequência

```
frequencia_grupo
```

---

# Regras

Nunca alterar

```
logradouro
```

Toda transformação ocorre em novas colunas.

---

# Futuras etapas

- Levenshtein
- Sinonímia
- Banco oficial de logradouros
- Correção baseada em frequência
- Correção assistida pelo usuário