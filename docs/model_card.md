# Model card — experimento inicial

**Responsável:** Lucas Menghi. **Processo:** desenvolvimento assistido por agente com revisão e aprovação humana. **Status:** experimental, sem aprovação operacional.

## Uso pretendido

Estimar valor bruto de compras em £ nos 30 dias seguintes para clientes identificados com compras nos 90 dias anteriores. Apoiar estimativas da população elegível; não estimar toda a receita da loja nem retorno causal de campanhas.

## Dados e avaliação

Online Retail, UCI, versão local identificada em `reports/run_manifest.json`. Desenvolvimento com referências de março a outubro de 2011. Backtests expansivos a partir de junho, exigindo maturação da variável resposta do treino. Novembro reservado, ainda não avaliado. Auditoria de cobertura/schema foi feita no arquivo inteiro.

Resultados estão em `reports/model_comparison.csv` e `reports/backtest_metrics.csv`; erros por recompra e faixa de gasto histórico em `reports/segment_metrics.csv`. São resultados de desenvolvimento sob regras provisórias, sem intervalos de confiança.

## Restrições

Ausência de IDs em parte das transações; curto histórico; sazonalidade; atacadistas; extremos e duplicatas não removidos na versão inicial; frete/ajustes ainda incluídos. Sem logs de disponibilidade ou revisões de registros. Generalização a outras lojas e períodos não comprovada.

## Próxima revisão

Revisar regras e seus impactos, discutir resultados por período e segmento, refinar candidatos sob validação temporal e aprovar configuração antes da avaliação final. Nenhum artefato é promovido automaticamente a produção.
