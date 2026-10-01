# Registro de decisões técnicas

| ID | Decisão experimental | Justificativa | Alternativa e condição de revisão |
|---|---|---|---|
| D01 | Variável resposta monetária em 30 dias | Escopo definido pelo responsável | Horizonte de 60 dias se eventos e estabilidade justificarem |
| D02 | Histórico de 90 dias; clientes identificados | Features disponíveis antes da previsão | Comparar janelas sem abrir o teste |
| D03 | Preservar duplicatas no experimento inicial | Não existe ID de linha que comprove repetição técnica | Relatório de sensibilidade quantifica deduplicação; decisão final pendente |
| D04 | Manter códigos especiais no experimento inicial | Preservar definição do discovery, sem alterar silenciosamente a variável resposta | Variante exclui lista explícita; natureza e impacto exigem revisão |
| D05 | Não subtrair devoluções de vendas históricas | Resposta bruta; cancelamento posterior não pode reescrever features passadas | Resposta líquida requer nova definição temporal e conciliação |
| D06 | Preservar extremos monetários | Remoção arbitrária altera população e objetivo | Investigar erros; ajuste de loss ou regra só após evidência |
| D07 | Folds expansivos com maturação de 30 dias | Simular previsão no futuro | Sem split aleatório, sem validação aleatória interna do boosting |
| D08 | Ridge, Tweedie e boosting com parâmetros fixos | Comparar linearidade, distribuição e não linearidade antes de tuning | Parâmetros não ótimos; refinamento posterior com validação temporal |
| D09 | RMSE, MAE e viés por período | Valor esperado, erro típico e desvio agregado são objetivos diferentes | Revisar loss se a finalidade de negócio mudar |
| D10 | Teste reservado em 01/11/2011 | Manter avaliação posterior às decisões de desenvolvimento | Auditoria estrutural global já ocorreu; distribuição da resposta não consultada |

## Disponibilidade e dependência

`InvoiceDate` é o horário do evento, sem timezone nem horário de ingestão na fonte. Assumimos disponibilidade imediata para esta reconstrução histórica; a hipótese não é verificável. `observed_span_days` mede alcance observado dentro de 90 dias, não tempo de relacionamento total.

Clientes repetem-se entre referências, pois o uso é prever clientes existentes. Não interpretamos linhas como amostras independentes nem calculamos intervalos ingênuos. As métricas agregadas ponderam cliente/referência; a tabela por mês deve acompanhar qualquer conclusão. Somar exposições não produz receita anual contábil.

## Por que estes candidatos?

- **Ridge:** referência linear regularizada. Escala estimada só no treino. Correlações entre janelas são esperadas; regularização não garante causalidade ou interpretação isolada de coeficientes.
- **Tweedie (power 1,5):** candidato para massa em zero e valores positivos contínuos, com link log. Não transforma a variável resposta com `log1p`; assume uma família ainda a validar. [API 1.2.2](https://scikit-learn.org/1.2/modules/generated/sklearn.linear_model.TweedieRegressor.html).
- **HistGradientBoosting:** candidato não linear com complexidade limitada. `early_stopping=False` evita validação interna aleatória; quantidade de iterações fixada. [API 1.2.2](https://scikit-learn.org/1.2/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html).

Nenhuma variante é declarada aprovada apenas por ter erro menor no desenvolvimento.

## Fechamento da versão v1

- **D11 — Definição preservada:** a autorização de finalizar foi aplicada ao escopo bruto existente. Não houve mudança silenciosa para receita líquida nem aprovação comercial inventada.
- **D12 — Busca limitada:** 23 configurações e cinco folds. Tweedie com log nas features foi o melhor regressor; ainda ficou 0,54% acima do RMSE do baseline no desenvolvimento.
- **D13 — Congelamento antes do teste:** commit `b723a39`, pipeline e dados identificados por hash. Novembro avaliado depois do congelamento, sem mudança do modelo.
- **D14 — Não promover ML:** RMSE em novembro 21,56% maior que a regra histórica. A rotina entrega ambos e recomenda a regra em coluna explícita. Menor MAE não substitui o critério pré-declarado.
- **D15 — Artefato avaliado preservado:** não retreinar com novembro nesta versão. Reconstrução usa parâmetros congelados e verifica equivalência da base de treino; não é nova seleção.

As pendências descritas no experimento inicial são históricas. O estado vigente está no model card e no notebook `03_final_model.ipynb`.
