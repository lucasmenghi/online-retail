# Protocolo da versão v1 — antes da avaliação final

## Autorização e definição congelada

Em 01/10/2026, Lucas solicitou finalizar a construção do modelo. A execução inclui refinamento, congelamento, teste temporal e entrega para previsão em lote. Isso não registra aprovação comercial específica de cada regra nem autorização de implantação produtiva.

A v1 mantém a definição trabalhada: valor bruto em £ de transações positivas, clientes identificados, sem prefixo C, quantidade e preço positivos. Duplicatas e códigos especiais permanecem incluídos. Cancelamentos futuros não reescrevem features anteriores. O valor previsto não é receita líquida nem valor de mercadorias excluindo taxas.

Essa definição viabiliza concluir uma versão consistente e comparável com os experimentos anteriores. Sua adequação comercial deve ser revisada antes de uso operacional. Alterá-la exige outra versão, incluindo nova variável resposta e avaliação apropriada.

## Busca e seleção

- 23 configurações declaradas em `src/model.py`: Ridge com features cruas ou log assinado, Tweedie com log nas features e boosting com perdas quadrática ou Poisson.
- Transformar features não transforma a variável resposta. Tweedie combina zeros e valores contínuos positivos; Poisson no boosting é uma função de perda candidata para média não negativa, sem afirmar que £ sejam contagens Poisson.
- Cinco folds expansivos: junho a outubro de 2011. Só entram no treino respostas maturadas até a referência de validação.
- Todos os candidatos usam as mesmas 18 features, população e observações. Padronização ajustada dentro do treino; nenhuma validação aleatória interna.
- Seleção do regressor pelo menor RMSE agregado das previsões fora do treino no desenvolvimento. Desempate determinístico pelo identificador. Referência obrigatória: gasto de 90 dias / 3.
- Resultados por fold, MAE e viés acompanham o ranking. Não retunar após consultar novembro. As métricas de seleção são otimistas por reutilização do desenvolvimento; o teste posterior serve à avaliação final.
- Candidatos com falha numérica, aviso de convergência ou previsões não finitas são registrados e excluídos, sem esconder a tentativa.

## Congelamento e avaliação

`reports/final/selection.json` registra configuração, regras, features, versões, SHA-256 dos dados e do código antes de calcular a resposta de novembro. O regressor é ajustado em março–outubro e salvo antes da abertura do teste.

Avaliar uma vez em referência 01/11/2011, resposta em `[01/11, 01/12)`, com acompanhamento completo. Comparar regressor congelado e baseline histórico; incluir erro por faixa de gasto e recompra, calibração por decis de previsão e bootstrap pareado por cliente para a diferença de RMSE. Esse intervalo é condicionado ao mês observado e não quantifica incerteza de outros regimes temporais.

Uma melhora observada em novembro não autoriza alegar generalização anual. Uma piora não autoriza trocar parâmetros e conservar o rótulo de teste independente. Documentar qualquer repetição técnica; repetir execução idêntica não fornece nova evidência.

## Entrega e aceitação técnica

Modelo serializado com hash, script de previsão que usa somente o passado, relatório final e model card. Testes: bordas, população, maturação, vazamento, paridade entre features de treino/inferência e serialização. O artefato entregue será o modelo efetivamente avaliado, sem retreino silencioso usando novembro.

Uso produtivo, SLO, fonte contínua, validação de disponibilidade, retenção de dados e aprovação de negócio permanecem fora desta conclusão técnica.
