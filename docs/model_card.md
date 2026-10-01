# Model card — regressão v1 concluída

**Responsável:** Lucas Menghi. **Processo:** desenvolvimento assistido por agente, com autorização humana de construção e finalização. **Status:** versão técnica concluída e avaliada; não aprovada para produção. A regra histórica permanece recomendada em relação ao regressor nesta versão.

## Definição e população

Estimar o valor bruto de compras em £ nos 30 dias seguintes para clientes identificados com transações positivas nos 90 dias anteriores. Features em `[t−90,t)` e variável resposta em `[t,t+30)`. Clientes sem recompra recebem zero apenas quando há horizonte completo.

Duplicatas e códigos especiais permanecem incluídos. Cancelamentos não são subtraídos da variável resposta, nem usados retroativamente para apagar features. A previsão não representa lucro, receita líquida ou efeito de campanha. A adequação dessa definição ao uso comercial precisa de revisão humana específica.

## Estimador e treino

Pipeline: transformação logarítmica assinada nas 18 variáveis explicativas → padronização → `TweedieRegressor(power=1.2, alpha=0.1, max_iter=3000)`. Não há transformação da variável resposta. Previsões negativas seriam truncadas em zero pela interface comum; o link log produz valores positivos.

Escolhido por RMSE em cinco backtests de junho a outubro, entre 23 configurações. Ajuste final em 15.376 observações cliente/referência, março–outubro de 2011. Artefato local: `artifacts/retail_v1.joblib`. Configuração e hash em `reports/final/selection.json` e `artifact_manifest.json`.

Congelamento registrado no commit `b723a39`, antes de abrir novembro. Não houve ajuste posterior ao teste. O artefato entregue é o avaliado, sem incorporar novembro ao treino.

## Avaliação final

Novembro: referência 01/11/2011, acompanhamento `[01/11,01/12)`, 2.461 clientes elegíveis; 57,09% sem recompra.

| Método | RMSE (£) | MAE (£) | Viés no total |
|---|---:|---:|---:|
| Regressão Tweedie v1 | 1.127,79 | 316,77 | −16,33% |
| Gasto em 90 dias / 3 | 927,77 | 326,20 | −2,12% |

O regressor reduz MAE em aproximadamente 2,89%, mas piora RMSE em 21,56% e subestima mais o total. Isso não atende ao objetivo inicial de superar a regra na previsão de valor esperado. A regressão é preservada como resultado auditável, não promovida como melhor método.

Bootstrap pareado de clientes: intervalo percentil de 95% para RMSE do regressor menos baseline de **£11,64 a £386,29**, 2.000 reamostragens, seed 42. O intervalo descreve incerteza amostral neste mês; não cobre sazonalidade futura, dependência entre empresas, seleção ou treinamento.

## Diagnósticos e interpretação

A regressão reduz erro nos clientes que não recompram, mas piora RMSE nos que recompram. O grupo com gasto histórico acima de £2.000 também tem RMSE maior. O total próximo do observado em um segmento não garante boas previsões individuais.

Importância por permutação foi calculada em outubro de desenvolvimento, antes do teste, usando um ajuste anterior a outubro. Ticket de 60 dias, gasto de 90 dias e ticket de 90 dias aparecem entre as maiores importâncias. Há forte correlação entre janelas; permutações podem criar combinações irreais e inflar importâncias. Isso mede dependência preditiva do modelo, não causalidade.

## Limitações e uso

Fonte histórica de uma loja, período curto, atacadistas, extremos e regras de valor bruto. Não há logs de ingestão: assumimos disponibilidade na data do evento. Não há comprovação de generalização anual nem a outras lojas.

`scripts/predict.py` entrega as duas previsões e identifica a regra histórica em `prediction_gbp`. O regressor aparece em `regressor_prediction_gbp`; nenhuma troca fica implícita. A rotina é local e batch, sem implantação de serviço, SLO ou aprovação operacional.

## Próxima versão

Qualquer refinamento adicional deve registrar que novembro já foi consultado. Para uma nova conclusão independente, obter período posterior completo ou outra fonte adequada; não renomear novembro como teste intocado. Rever definição comercial e disponibilização dos eventos antes de promover qualquer método.
