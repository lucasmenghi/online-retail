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

As datas registram a sessão de trabalho. A autorização de continuar permite experimentos reversíveis; não equivale à aprovação de cada hipótese comercial ou do desempenho de um modelo.

## Pontos de revisão humana

1. **Definição da variável resposta:** tratamento de frete, ajustes, devoluções e duplicatas. Status: proposta experimental; aprovação final pendente.
2. **Seleção do modelo:** revisar backtests, métricas, segmentos e sensibilidade antes de congelar a configuração. Status: comparação inicial, sem aprovação final.
3. **Avaliação final:** congelar regras e modelo antes de abrir novembro; registrar qualquer reutilização. Status: não executada.
4. **Uso operacional:** avaliar monitoramento, custos, requisitos de dados e limites. Status: não autorizado nem implementado.

## Rastreabilidade

`reports/run_manifest.json` identifica dados, versões, features e parâmetros do experimento. `docs/decisions.md` registra justificativas e alternativas. As saídas dos notebooks e relatórios agregados permitem revisar o trabalho sem publicar registros individuais de previsões.

Não há alegação de auditoria externa, conformidade certificada ou resultados comerciais comprovados.
