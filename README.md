# Online Retail · previsão de compras em 30 dias

![Online Retail — Previsão de compras em 30 dias com regressão e CRISP-DM](reports/figures/executive-cover.png)

Construção e avaliação de regressão para estimar o valor bruto comprado por cliente nos próximos 30 dias, usando 90 dias de histórico. Desenvolvimento organizado pelo CRISP-DM, da definição do problema à entrega de inferência batch.

**Autoria:** Lucas Menghi desenvolveu esta modelagem em um fluxo governado, com assistência de agente de IA e autorização humana. O agente implementou, explicou e verificou as alternativas; decisões, autorizações e limites de aprovação estão em [Governança](docs/governance.md). Não há certificação externa nem aprovação de implantação produtiva.

## Resultado da versão v1

**Construção concluída. O ML não superou a regra histórica no critério principal.** Entre 23 configurações, a regressão Tweedie com transformação logarítmica nas features foi escolhida pelo RMSE de desenvolvimento. Foi congelada antes de avaliar novembro de 2011, sem ajustes posteriores.

| Método — novembro, 2.461 clientes | RMSE (£) | MAE (£) | Viés no total |
|---|---:|---:|---:|
| Regressão Tweedie v1 | 1.127,79 | 316,77 | −16,33% |
| Gasto dos últimos 90 dias / 3 | **927,77** | 326,20 | **−2,12%** |

A regressão piorou RMSE em 21,56%, embora tenha reduzido MAE. A entrega preserva o regressor treinado e recomenda a regra histórica nesta versão. O notebook final explica a decisão, segmentos, incerteza e limitações. Um resultado negativo de comparação não é escondido nem corrigido ajustando o modelo no teste.

## Percurso CRISP-DM

1. [00_discovery.ipynb](00_discovery.ipynb): entendimento do negócio e dos dados.
2. [01_preparation.ipynb](01_preparation.ipynb): qualidade, sensibilidade e features temporais.
3. [02_modeling.ipynb](02_modeling.ipynb): baselines e primeira comparação.
4. [03_final_model.ipynb](03_final_model.ipynb): refinamento, configuração congelada, avaliação final e entrega.

Os três primeiros notebooks preservam o estado histórico de cada etapa. O estado vigente está no quarto notebook e no [model card](docs/model_card.md).

```text
src/                     Features, estimadores, avaliação e inferência
tests/                   Contratos temporais, numéricos e de serialização
scripts/                 Execução, refinamento, reconstrução e previsão
docs/                    Governança, decisões, model card e contrato batch
reports/final/           Busca, congelamento e resultados finais agregados
data/raw/                Fonte local, não versionada
data/processed/          Dados processados locais, não versionados
artifacts/               Modelo treinado local, não versionado
```

## Reproduzir e prever

Python 3.11; versões fixadas em `requirements.txt`. Consulte [dados e atribuição](data/README.md).

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts/run_notebooks.py
```

Os notebooks reproduzem análises e leem os relatórios finais congelados; não reabrem automaticamente a busca nem o teste. Com o CSV disponível, reconstrua o artefato conforme a configuração registrada:

```powershell
.venv\Scripts\python scripts/rebuild_artifact.py
.venv\Scripts\python scripts/predict.py --as-of 2011-11-01 --output reports/predictions/november.csv
```

Se a reconstrução gerar manifesto local, acrescente `--manifest artifacts/rebuilt_manifest.json`. O CSV de saída identifica separadamente a previsão do regressor e da regra recomendada. Detalhes em [contrato batch](docs/batch_contract.md).

O comando `scripts/finalize_model.py tune` foi usado antes do teste, seguindo o [protocolo](docs/finalization_protocol.md). As proteções impedem sobrescrever a seleção ou reavaliar novembro como se fosse uma nova avaliação independente.

## Contrato e limites

Cada observação é cliente × referência mensal. Features usam `[t−90,t)` e variável resposta `[t,t+30)`. Clientes identificados sem recompra recebem zero com acompanhamento completo. A v1 preserva duplicatas e códigos especiais; soma transações positivas sem deduzir devoluções. Não é previsão de receita líquida nem de toda a loja.

Histórico curto, sazonal, com atacadistas e extremos; ausência de horário de ingestão. Um mês de teste não demonstra generalização anual. Novembro já foi consultado e não pode voltar a ser chamado de teste intocado em uma nova rodada de ajustes.

Fonte: Chen, D. (2015). [Online Retail, UCI](https://doi.org/10.24432/C5BW33), CC BY 4.0. A licença dos dados não implica automaticamente uma licença para o código.
