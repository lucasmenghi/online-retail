# Contrato de previsão e monitoramento proposto

## Entrada

CSV no formato documentado em `data/README.md`, com pelo menos 90 dias de cobertura antes da referência. `--as-of` usa o relógio sem timezone da fonte; todas as features ignoram eventos a partir dessa data. Não se exige informação futura para prever.

Por padrão, o início do último dia observado é o limite conservador de cobertura. `--observed-through` permite declarar outro limite exclusivo quando o operador conhece a completude da fonte. Essa declaração não prova continuidade nem ausência de registros atrasados.

Datas inválidas, features não finitas, colunas ausentes, incompatibilidade de versões ou hash divergente do modelo causam erro explícito. Referências anteriores à disponibilidade histórica do modelo são rejeitadas. Arquivos de saída existentes não são sobrescritos.

## Saída

Uma linha por cliente elegível, identificador, referência e fim exclusivo do horizonte. `regressor_prediction_gbp` contém a regressão congelada; `baseline_prediction_gbp` contém gasto de 90 dias / 3; `prediction_gbp` contém o método recomendado **last_90d_div3**, selecionado por evidência comparativa, sem implantação produtiva.

Sem clientes elegíveis, a saída pode conter apenas o cabeçalho. Previsões individuais são gravadas localmente em diretório ignorado pelo Git.

## Execução

```powershell
python scripts/predict.py --as-of 2011-11-01 --output reports/predictions/november.csv
```

O artefato local é ignorado pelo Git. Para reconstruir em outro checkout com os dados e ambiente corretos:

```powershell
python scripts/rebuild_artifact.py
```

O script compara a base de treino normalizada, permitindo diferenças de formatação do CSV sem aceitar dados de treinamento diferentes. Se o hash de serialização mudar, um manifesto local é criado; use `--manifest artifacts/rebuilt_manifest.json`. O manifesto da execução original permanece inalterado. Só carregue artefatos joblib de origem confiável.

## Verificação executada

Testes de janelas, população, maturação, features finitas, serialização, ordenação de colunas e paridade treino/inferência. A rotina batch reproduziu exatamente as previsões do teste para 2.461 clientes em novembro. Não há benchmark representativo de serviço ou carga concorrente; não se declara SLO.

## Monitoramento para eventual operação

- Em cada lote: cobertura declarada, volume de clientes, percentual sem ID, cancelamentos, nulos, datas máximas, soma e quantis de previsão, versão e hash do artefato.
- Após maturação de 30 dias: RMSE, MAE, viés agregado e por faixa de gasto, comparados com a regra histórica.
- Comparar distribuição das features com `reports/final/training_feature_profile.csv`. Mudança de distribuição é sinal de investigação, não comprovação de degradação ou justificativa automática de retreino.
- Limites de alerta e responsáveis precisam ser definidos com a operação. Falha de dados não deve produzir previsão silenciosa.

O método histórico é a recomendação desta avaliação, não um fallback silencioso diante de erro técnico: o comando falha explicitamente se a construção das features ou o carregamento do regressor não passar nas verificações.
