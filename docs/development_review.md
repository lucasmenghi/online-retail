# Revisão do experimento inicial

## Evidência executada

Três notebooks executados sem erros e quatro testes de contrato temporal aprovados. Fonte local com SHA-256 em `reports/run_manifest.json`. Backtests de junho a outubro de 2011, com 10.027 observações cliente/referência; novembro não avaliado.

| Método | RMSE (£) | MAE (£) | Viés agregado (%) |
|---|---:|---:|---:|
| Gasto em 90 dias / 3 | 1.264,07 | 298,19 | +12,88 |
| HistGradientBoosting | 1.283,35 | 283,63 | −13,19 |
| Ridge | 1.342,68 | 282,06 | −8,52 |
| Gasto em 30 dias | 1.630,30 | 361,40 | +25,16 |
| Média do treino | 1.645,33 | 369,46 | −16,48 |
| Zero | 1.668,30 | 278,82 | −100,00 |
| Tweedie inicial | 22.100,34 | 881,32 | +198,03 |

Os números resumem os folds sob regras provisórias. Não são desempenho no teste final. A dependência entre clientes e períodos impede inferir significância da diferença diretamente dessa tabela.

## Interpretação

A regra histórica supera todos os modelos no RMSE agregado inicial. O boosting fica cerca de 1,53% acima do RMSE da regra; reduz MAE, mas subestima o total. Nenhum modelo foi promovido.

Prever zero tem o menor MAE entre os candidatos, mas subestima todo o valor comprado. Isso evidencia por que MAE isolado não atende ao planejamento de receita esperada nesta população.

Tweedie apresentou erro elevado sem avisos de convergência. Convergência numérica não garante extrapolação adequada. O link exponencial com features de cauda longa é uma hipótese para investigar, não uma causa demonstrada. Não é candidato a promoção nesta configuração. Próximo experimento possível: diagnosticar maiores erros, transformar features monetárias e comparar regularização em folds temporais, sem alterar a variável resposta ou abrir novembro.

## Sensibilidade e qualidade

No desenvolvimento anterior a novembro, deduplicar linhas exatas reduz o valor positivo em 0,24%; excluir a lista de códigos especiais reduz em 1,74%; ambas as ações reduzem em 1,98%. Impactos agregados pequenos não excluem mudanças relevantes por cliente. A tabela completa está em `reports/rule_sensitivity.csv`.

Uma venda de £77.183,60 em 18/01/2011 tem um cancelamento candidato 16 minutos depois, com o mesmo cliente, produto, quantidade absoluta e preço. A coincidência não é uma ligação documental definitiva. A regra bruta mantém esse lançamento; a revisão da resposta deve decidir como lidar com reversões sem reescrever features históricas usando eventos futuros.

## Próxima decisão

Lucas deve revisar as evidências para fechar o significado comercial de valor comprado: manter transações positivas brutas ou adotar uma definição com reversões e exclusão de ajustes. Os experimentos atuais usam a primeira definição, ainda provisória. Depois dessa revisão, refinar as regressões e avaliar estabilidade por mês e segmento. A decisão de promover um modelo permanece pendente.
