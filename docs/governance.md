# Governança do desenvolvimento

Lucas Menghi desenvolve a modelagem com assistência de agente e aprovação humana ao longo do fluxo. O processo usa o CRISP-DM e instruções metodológicas da biblioteca `data-science-skills`.

## Responsabilidades

| Papel | Responsabilidade |
|---|---|
| Lucas Menghi | Definir objetivo, revisar critérios, aprovar regras de negócio e promoção do modelo |
| Agente de desenvolvimento | Implementar, explicar alternativas, testar, documentar evidências e sinalizar incertezas |
| Evidência reproduzível | Código, dados identificados por hash, versões, testes e resultados agregados |

## Registro de autorizações humanas

| Data | Evidência | Escopo |
|---|---|---|
| 2026-10-01 | Solicitação explícita de iniciar o notebook com CRISP-DM e regressão | Desenvolvimento de valor comprado por cliente em 30 dias |
| 2026-10-01 | Solicitação explícita de organizar e subir o repositório `lucasmenghi/online-retail`, ajustar a terminologia e continuar o fluxo | Publicação do trabalho e continuação dos experimentos |
| 2026-10-01 | Solicitação explícita: “vamos finalizar a construção do modelo” | Finalização técnica, refinamento, congelamento, avaliação e entrega batch sob o escopo existente |

As datas registram a sessão de trabalho. A autorização de continuar permite experimentos reversíveis; não equivale à aprovação de cada hipótese comercial ou do desempenho de um modelo.

## Pontos de revisão humana

1. **Definição da variável resposta:** definição bruta existente preservada e congelada para concluir v1. Adequação comercial de frete, ajustes, devoluções e duplicatas ainda não aprovada para operação.
2. **Seleção do modelo:** 23 configurações comparadas pelo agente sob autorização de finalização; Tweedie selecionado no desenvolvimento. Não atribuir ao responsável uma aprovação manual de parâmetros que não ocorreu.
3. **Avaliação final:** configuração congelada no commit `b723a39`; novembro avaliado sem retuning. Resultado desfavorável ao ML registrado, com recomendação de manter a regra histórica.
4. **Uso operacional:** rotina batch local entregue e testada. Implantação produtiva, SLO e aprovação comercial não autorizados nem comprovados.

## Rastreabilidade

`reports/run_manifest.json` preserva o experimento inicial. `reports/final/selection.json`, `artifact_manifest.json` e `evaluation.json` registram a versão final. `docs/decisions.md` registra justificativas e alternativas. As saídas dos notebooks e relatórios agregados permitem revisar o trabalho sem publicar registros individuais de previsões.

Não há alegação de auditoria externa, conformidade certificada ou resultados comerciais comprovados.
