# Dados

Fonte: Chen, D. (2015), [Online Retail — UCI](https://doi.org/10.24432/C5BW33), CC BY 4.0.

O CSV original permanece local e é ignorado pelo Git. Coloque `Online Retail.csv` em `data/raw/` ou na raiz do projeto. O arquivo utilizado tem separador `;`, decimal `,`, codificação UTF-8 e datas `%d/%m/%Y %H:%M`.

Para reproduzir a partir do XLSX oficial, baixe o arquivo na UCI e execute:

```powershell
python scripts/convert_uci.py "caminho/Online Retail.xlsx"
```

O hash do CSV convertido pode diferir do arquivo local, mesmo com dados equivalentes. Registre o hash de cada execução; não declare identidade de versões apenas pelo número de linhas. Arquivos processados e previsões individuais também ficam fora do Git; relatórios agregados são versionados.
