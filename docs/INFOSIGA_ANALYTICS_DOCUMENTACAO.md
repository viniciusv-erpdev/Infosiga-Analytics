# Infosiga Analytics — Documentação Técnica

## 1. Visão geral

O **Infosiga Analytics** é uma aplicação web Django para ingestão, processamento,
normalização e análise de dados de sinistros de trânsito.

O sistema recebe arquivos CSV/XLSX, aplica filtros e um pipeline de pré-processamento
de logradouros, persiste o dataset original e o resultado processado e permite ao
usuário autenticado consultar os próprios datasets.

A arquitetura foi construída de forma incremental, priorizando:

- simplicidade;
- separação de responsabilidades;
- baixo acoplamento;
- persistência adequada ao volume de dados;
- evolução gradual para Review, mapas e dashboards;
- evitar complexidade desnecessária para o escopo do projeto.

---

## 2. Arquitetura atual

Fluxo principal:

```text
Usuário autenticado
        |
        v
      Home
        |
        v
 Upload CSV/XLSX
        |
        v
     file_loader
        |
        +----> Dataset original
        |
        v
      filtros
        |
        v
 run_preprocessing()
        |
        +--> normalização
        +--> limpeza semântica
        +--> correções manuais
        +--> matching/fuzzy
        |
        v
 DataFrame processado
        |
        v
 Parquet processado
        |
        v
      Dataset
        |
        +--> /datasets/
        |
        +--> /datasets/<id>/
        |
        +--> Download
```

### Separação conceitual

**Dataset**
- representa os dados persistidos;
- pertence a um usuário;
- mantém referência ao arquivo original;
- mantém referência ao resultado processado;
- funciona como unidade de persistência e histórico do processamento.

**DataFrame**
- representa os dados em memória durante o processamento;
- recebe filtros e regras de negócio;
- é produzido e transformado pelo pipeline;
- posteriormente é persistido como Parquet.

Essa separação evita depender da sessão HTTP para armazenar grandes conjuntos
de dados.

---

## 3. Tecnologias e dependências

### Backend

- Python 3.13+
- Django
- Pandas
- RapidFuzz
- SQLite no desenvolvimento atual
- Parquet para persistência dos DataFrames processados

### Frontend

- HTML
- CSS
- Bootstrap 5
- Bootstrap Icons
- JavaScript quando necessário

### Desenvolvimento

- VS Code
- Git/GitHub
- ambiente virtual Python (`.venv`)
- DBeaver pode ser utilizado para inspeção de banco

### Formatos de entrada

- CSV
- XLSX

### Formato de persistência dos dados processados

- Parquet

---

## 4. Estrutura conceitual de diretórios

A estrutura relevante segue aproximadamente:

```text
analytics/
├── models.py
├── forms.py
├── views/
│   ├── home.py
│   ├── auth.py
│   ├── datasets.py
│   └── review.py
│
├── services/
│   ├── dataset_service.py
│   ├── review_service.py
│   ├── file_loader.py
│   └── filters.py
│
├── persistence/
│   └── datasets.py
│
├── pipeline.py
│
├── services/
│   └── preprocessing/
│       ├── address_normalizer.py
│       ├── address_semantic_cleaner.py
│       ├── address_matcher.py
│       └── apply_manual_corrections.py
│
├── templates/
│   └── analytics/
│       ├── base.html
│       ├── home.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       └── datasets/
│           ├── list.html
│           └── detail.html
│
└── tests.py
```

Observação: a organização exata pode conter outros arquivos auxiliares não
listados neste documento.

---

## 5. Modelos principais

### Dataset

Responsável por representar um conjunto de dados enviado pelo usuário.

Campos principais:

- `usuario`: usuário proprietário;
- `nome_original`: nome original do arquivo;
- `arquivo`: arquivo original persistido;
- `quantidade_registros`: quantidade de registros do dataset;
- `criado_em`: data de criação;
- `atualizado_em`: última atualização;
- `resultado_processado`: arquivo Parquet produzido pelo preprocessing.

O relacionamento com o usuário garante isolamento dos datasets entre contas.

### AddressCorrection

Armazena correções de logradouro utilizadas pelo sistema.

Conceitualmente:

```text
logradouro original/limpo
        |
        v
correção cadastrada
        |
        +--> PENDENTE
        +--> APROVADO
        +--> REJEITADO
```

Correções manuais aprovadas possuem precedência sobre sugestões automáticas.

### CorrectionAudit

Mantém o histórico das alterações realizadas nas correções.

A gravação das auditorias já utiliza operação atômica.

---

## 6. Pipeline de preprocessing

O pipeline principal está em `pipeline.py`.

Ordem atual:

```text
normalize_address
        |
        v
clean_semantic_address
        |
        v
apply_manual_corrections
        |
        v
regularize_addresses
```

### normalize_address

Responsável pela normalização determinística do logradouro.

Exemplos de operações incluem padronização de abreviações e representação textual.

### clean_semantic_address

Executa limpeza semântica depois da normalização.

O resultado é armazenado em:

```text
logradouro_limpo
```

### apply_manual_corrections

Consulta as correções persistidas e aplica somente as correções aprovadas.

Quando uma correção manual é aplicada:

```text
logradouro_canonico = valor corrigido
correcao_manual_aplicada = True
```

### address_matcher

Realiza agrupamento e matching fuzzy.

A sugestão automática é armazenada separadamente:

```text
logradouro_sugerido
```

Isso é conceitualmente diferente de:

```text
logradouro_canonico
```

#### Regra importante

- `logradouro_sugerido`: resultado automático do matcher/fuzzy;
- `logradouro_canonico`: resultado de correção manual aprovada;
- `correcao_manual_aplicada`: indica que uma correção manual foi aplicada.

O sistema não deve tratar sugestão fuzzy como correção canônica.

---

## 7. Upload e processamento

O fluxo atual de upload ocorre essencialmente em `file_loader.py`.

Etapas:

1. validar formulário;
2. receber arquivo;
3. identificar extensão;
4. carregar CSV/XLSX em DataFrame;
5. aplicar filtros de negócio;
6. criar `Dataset` para o usuário autenticado;
7. executar `run_preprocessing()`;
8. salvar o DataFrame processado como Parquet;
9. associar o Parquet ao Dataset;
10. redirecionar o usuário para a Home.

O Dataset é criado com o usuário obtido através de:

```python
request.user
```

Não deve ser solicitado ao usuário que digite manualmente seu identificador.

---

## 8. Persistência Parquet

O módulo:

```text
analytics/persistence/datasets.py
```

é responsável pela persistência dos DataFrames em Parquet.

Principais responsabilidades:

- salvar DataFrame como Parquet;
- carregar Parquet;
- criar Dataset;
- salvar resultado processado;
- carregar resultado processado.

A camada de serviço:

```text
analytics/services/dataset_service.py
```

expõe essas operações para as views e demais componentes da aplicação.

Essa separação mantém detalhes de armazenamento fora das views.

---

## 9. DatasetService

O `DatasetService` atua como camada de serviço para operações relacionadas
a datasets.

Responsabilidades atuais:

- criar Dataset a partir de upload;
- listar datasets de um usuário;
- salvar DataFrame processado;
- carregar DataFrame processado.

As views não devem manipular diretamente detalhes de persistência Parquet
quando uma operação correspondente estiver disponível no service.

---

## 10. Autenticação

A autenticação é baseada no sistema de autenticação do Django.

Implementações atuais:

- login;
- registro;
- logout;
- proteção das views que exigem usuário autenticado.

Arquivo principal:

```text
analytics/views/auth.py
```

Inclui formulários derivados dos formulários padrão do Django para adaptação
visual ao Bootstrap.

O usuário autenticado é a origem da propriedade dos datasets e deve também
ser utilizado futuramente para registrar o autor das alterações no Review.

---

## 11. Telas atuais

### Home

Responsabilidades:

- receber CSV/XLSX;
- permitir seleção dos filtros;
- iniciar o processamento;
- informar o resultado do upload;
- direcionar o usuário para o Dataset criado.

A antiga pré-visualização pesada baseada em sessão deixou de ser o principal
mecanismo de visualização dos dados.

Isso foi necessário porque datasets reais podem possuir centenas de milhares
de registros.

### Login

Permite autenticação de usuários existentes.

### Registro

Permite criação de novas contas.

### Logout

Encerra a sessão autenticada.

### Meus datasets — `/datasets/`

Lista os datasets pertencentes ao usuário autenticado.

Não deve permitir que um usuário visualize datasets de outra conta.

### Detalhe do Dataset — `/datasets/<id>/`

Permite:

- visualizar o resultado processado;
- consultar registros paginados;
- visualizar informações básicas;
- baixar o resultado processado;
- acessar somente datasets pertencentes ao usuário autenticado.

A paginação é importante para evitar renderização de milhares de registros
em uma única página.

---

## 12. Visualização atual dos dados

A primeira visualização relevante do resultado processado utiliza principalmente:

- `logradouro`;
- `logradouro_sugerido`;
- `logradouro_canonico`;
- `correcao_manual_aplicada`.

Campos internos como:

- `logradouro_normalizado`;
- `logradouro_limpo`;
- `similaridade`;
- `frequencia_grupo`;

não são prioritários para o usuário final no MVP.

Esses campos continuam existindo no DataFrame porque são importantes para
o funcionamento e diagnóstico do pipeline.

---

## 13. Review

A tela Review já possui infraestrutura para:

- consultar registros;
- abrir interface de correção;
- enviar alterações;
- persistir correções;
- manter auditoria.

Porém, ainda existem melhorias planejadas.

### Estado atual

O Review ainda possui lógica antiga em alguns pontos, especialmente a entrada
manual do autor da correção.

### Próximas melhorias

- utilizar diretamente `request.user`;
- remover entrada manual de usuário/autor;
- melhorar pesquisa por logradouro;
- permitir pesquisa por sugestão fuzzy;
- permitir pesquisa por correção manual/canônica;
- trabalhar com paginação server-side;
- refinar interface;
- manter histórico de auditoria.

Essas melhorias devem ser feitas posteriormente, depois da estabilização da
visualização dos datasets.

---

## 14. Filtros

Os filtros são aplicados antes do preprocessing.

Atualmente existem filtros relacionados a:

- tipo de via;
- tipo de sinistro.

O filtro é aplicado ao DataFrame original carregado antes da execução completa
do pipeline.

Isso reduz a quantidade de dados que precisa passar pelas etapas posteriores.

---

## 15. Workflow completo

### Upload

```text
Usuário
  |
  v
Login
  |
  v
Home
  |
  v
Seleciona arquivo + filtros
  |
  v
file_loader
  |
  v
DataFrame original
  |
  v
Filtros
  |
  v
Dataset criado
  |
  v
run_preprocessing()
  |
  +--> normalização
  +--> limpeza
  +--> correções manuais
  +--> fuzzy matching
  |
  v
DataFrame processado
  |
  v
Parquet
  |
  v
Dataset.resultado_processado
```

### Consulta

```text
Usuário
  |
  v
Meus datasets
  |
  v
Seleciona Dataset
  |
  v
DatasetService
  |
  v
Carrega Parquet
  |
  v
Paginação
  |
  v
Tabela
```

### Correção

```text
Registro
  |
  v
Review
  |
  v
usuário autenticado
  |
  v
correção
  |
  v
AddressCorrection
  |
  v
CorrectionAudit
  |
  v
próximo preprocessing utiliza correção aprovada
```

---

## 16. Princípios arquiteturais

### Separação de responsabilidades

Views cuidam de HTTP e apresentação.

Services coordenam regras de aplicação.

Persistence cuida do armazenamento.

Preprocessing cuida da transformação dos dados.

Models representam estado persistente.

### SOLID proporcional ao projeto

O projeto não busca uma arquitetura excessivamente abstrata.

A regra é criar abstrações quando existe uma responsabilidade real a separar,
não simplesmente criar camadas por formalidade.

### Incrementalidade

Alterações devem preferencialmente:

- preservar código existente;
- modificar pequenas partes;
- evitar refatorações amplas sem necessidade;
- manter testes próximos da funcionalidade alterada.

---

## 17. Armazenamento

Existem dois tipos principais de dados persistidos:

### Banco Django

Utilizado para:

- usuários;
- datasets;
- correções;
- auditoria;
- metadados.

### Arquivos

Utilizados para:

- arquivo original enviado;
- resultado processado em Parquet.

Essa divisão evita colocar DataFrames grandes diretamente no banco relacional.

O Parquet é particularmente adequado para datasets analíticos porque reduz
o custo de armazenamento e permite leitura eficiente.

---

## 18. Considerações de desempenho

O sistema não deve:

- colocar DataFrames grandes na sessão;
- renderizar centenas de milhares de registros de uma vez;
- carregar todos os registros apenas para montar uma página;
- duplicar desnecessariamente grandes arquivos.

O sistema deve:

- persistir resultados processados em Parquet;
- utilizar paginação;
- carregar apenas o necessário para a visualização;
- manter o banco relacional focado em metadados e entidades de negócio.

---

## 19. Segurança

Regras importantes:

- endpoints protegidos devem exigir autenticação;
- Dataset deve ser filtrado pelo usuário proprietário;
- download deve verificar propriedade;
- não confiar em IDs enviados pelo cliente para determinar o proprietário;
- correções devem registrar o usuário autenticado;
- operações de auditoria devem permanecer atômicas.

---

## 20. Estado atual e próximos passos

### Concluído

- autenticação;
- registro;
- logout;
- Dataset;
- associação Dataset ↔ usuário;
- upload;
- filtros;
- preprocessing;
- correções manuais;
- auditoria atômica;
- persistência Parquet;
- DatasetService;
- carregamento de resultado processado;
- listagem de datasets;
- detalhe de dataset;
- paginação inicial;
- download do resultado processado;
- separação entre sugestão fuzzy e correção canônica.

### Próxima fase

Antes de mapa e dashboard, recomenda-se:

1. estabilizar e redesenhar a tela Review;
2. substituir autor manual por usuário autenticado;
3. adicionar pesquisa e filtros no Review;
4. melhorar a UI das telas existentes;
5. validar completamente o fluxo de correção;
6. somente depois avançar para mapa e dashboards.

### Funcionalidades futuras

- mapa Leaflet;
- latitude/longitude;
- dashboards analíticos;
- filtros avançados;
- indicadores;
- possíveis mecanismos de limpeza/retention dos arquivos antigos.

---

## 21. Regras para futuras alterações

Antes de implementar uma funcionalidade:

1. identificar qual camada é responsável;
2. verificar se já existe service/persistence reutilizável;
3. evitar colocar regra de negócio em template;
4. evitar colocar persistência diretamente na view;
5. não duplicar lógica existente;
6. preservar a distinção entre sugestão automática e correção manual;
7. testar isoladamente antes de integrar ao fluxo real;
8. executar `python manage.py check` quando o ambiente estiver completo;
9. testar com dataset pequeno antes de datasets reais;
10. evitar introduzir complexidade que não tenha benefício para o MVP.

---

## 22. Observação sobre ambiente

O projeto é desenvolvido inicialmente em Windows, mas a arquitetura deve permanecer
compatível com implantação futura em Linux em um computador antigo.

Por isso, deve-se evitar dependências desnecessariamente pesadas e soluções que
exijam infraestrutura complexa.

O armazenamento em Parquet e o uso do SQLite no desenvolvimento são compatíveis
com essa filosofia para o escopo atual.

## 23. Correções futuras

1. Alterar a geração dos arquivos Parquet para utilizar caminhos exclusivos por Dataset, evitando colisões quando diferentes uploads possuem o mesmo nome original.

2. Tornar o caminho do Parquet único por Dataset, preferencialmente incorporando o dataset.id ao nome ou utilizando um diretório próprio para cada Dataset.

3. Conectar a edição manual à interface de detalhes do dataset somente após estabilizar e testar completamente a camada de persistência.

4. Centralizar no DatasetService a coordenação entre edição do registro, atualização de correção e auditoria, mantendo as camadas de persistence responsáveis apenas pelo armazenamento.
