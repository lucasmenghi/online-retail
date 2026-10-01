# Online Retail · previsão de compras em 30 dias

Modelo de regressão para estimar o valor bruto comprado por cliente nos 30 dias seguintes, com histórico de 90 dias e validação temporal. O desenvolvimento segue o CRISP-DM.

**Autoria:** Lucas Menghi desenvolve esta modelagem em um fluxo governado, com assistência de agente de IA e aprovação humana. O agente propõe e implementa análises, explica decisões e executa verificações; Lucas define o escopo, revisa as evidências e aprova as decisões de negócio e a promoção de modelos. Autorizações e pendências estão em [Governança](docs/governance.md). Isso não representa certificação externa nem aprovação produtiva.

## Estado atual

- Entendimento do negócio e dos dados documentado e executado.
- Preparação experimental com regras explícitas, análise de sensibilidade e features temporais.
- Comparação inicial de baselines e regressões em backtests de desenvolvimento.
- Novembro de 2011 reservado: sem avaliação da variável resposta de teste nesta etapa.
- Regras finais e modelo para uso operacional ainda pendentes de revisão humana.

## Organização

```text
00_discovery.ipynb              Entendimento do negócio e dos dados
01_preparation.ipynb            Qualidade, sensibilidade, features e contrato temporal
02_modeling.ipynb               Baselines e regressões em desenvolvimento
src/                           Funções reutilizáveis
tests/                         Contratos de janelas, população e vazamento
scripts/                       Conversão e execução dos notebooks
docs/                          Governança, decisões e model card
reports/                       Resultados agregados e manifesto da execução
data/raw/                      Fonte local, não versionada
data/processed/                Base cliente/referência local, não versionada
```

## Reproduzir

Ambiente validado: Python 3.11. Consulte [dados e atribuição](data/README.md).

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts/run_notebooks.py
```

Também é possível selecionar a `.venv` como kernel e executar os notebooks em ordem. Nenhum script instala dependências automaticamente ou baixa dados sem uma ação explícita.

## Contrato analítico

Cada linha representa cliente × referência mensal. Features usam `[t−90 dias, t)` e a variável resposta usa `[t, t+30 dias)`. Clientes elegíveis sem compra futura recebem zero somente com acompanhamento completo. Transações sem identificação não compõem a população individual.

O experimento inicial preserva duplicatas e códigos especiais de transações positivas, conforme a regra inicial do discovery. Variantes avaliam exclusões, sem apresentá-las como aprovadas. A variável resposta representa valor bruto registrado, não receita líquida, lucro ou efeito de campanhas.

RMSE em £ orienta inicialmente a comparação para valor esperado; MAE, viés e resultados por período complementam a avaliação. Previsões monetárias negativas são truncadas em zero, com a incidência reportada. Valores monetários reais da variável resposta não são truncados.

## Limitações

Histórico curto e sazonal, uma única loja, muitos zeros, valores extremos e ausência de horário de disponibilidade dos registros. A validação assume disponibilidade na data do evento; essa hipótese não é comprovada pelo arquivo. Resultados de desenvolvimento não são resultados do teste final.

Fonte: Chen, D. (2015). [Online Retail, UCI](https://doi.org/10.24432/C5BW33), CC BY 4.0. A licença da fonte não implica automaticamente uma licença para o código deste repositório.
