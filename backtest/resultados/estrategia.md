# Simulación de la estrategia · velas M15 · últimos 21 días

Generado: 2026-11-13 11:41 UTC

Lote 0,01 (1 USD de precio = 1 USD de resultado). Se entra en el primer precio de la vela siguiente a la señal. Una cobertura opuesta del mismo tamaño congela la pérdida en ese punto, así que se simula como un cierre a −10 (en la realidad cuesta además otro spread y el swap mientras está abierta). **Peor flotante** es la peor pérdida no realizada que tuvo una operación antes de cerrar. **Entradas al azar con resultado igual o mejor**: si es alto (por ejemplo, más de 10–20 %), la señal no le gana al azar.

## Deriv · frxXAUUSD

1356 velas M15 · costo por posición 0.40 USD · una canasta a la vez · comparación con 500 pruebas de entradas al azar

### +10 / cobertura a −10 (= pérdida fija de 10)

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 69 | 57 % | +70 USD | +1.01 | -11 | -89 | -11 | -28 USD | 12 % |
| a favor del color de la vela | 69 | 59 % | +101 USD | +1.47 | -17 | -83 | -16 | -28 USD | 6 % |


### +20 / cobertura a −10 (= pérdida fija de 10)

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 59 | 44 % | +172 USD | +2.91 | -11 | -63 | -11 | -40 USD | 2 % |
| a favor del color de la vela | 58 | 41 % | +106 USD | +1.83 | -17 | -86 | -16 | -40 USD | 10 % |


### +10 sin cobertura, hasta 4 horas

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 55 | 67 % | -6 USD | -0.10 | -82 | -167 | -87 | -80 USD | 26 % |
| a favor del color de la vela | 62 | 65 % | -7 USD | -0.12 | -56 | -95 | -63 | -80 USD | 26 % |


### Promediar: otra 0,01 cada −10 (máx. 3), todo en +10, corte a −40

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 57 | 61 % | -181 USD | -3.18 | -92 | -314 | -92 | -78 USD | 70 % |
| a favor del color de la vela | 78 | 31 % | -134 USD | -1.72 | -92 | -265 | -92 | -78 USD | 61 % |


## Binance Futuros · XAUUSDT (volumen negociado)

1968 velas M15 · costo por posición 0.40 USD · una canasta a la vez · comparación con 500 pruebas de entradas al azar

### +10 / cobertura a −10 (= pérdida fija de 10)

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 131 | 52 % | -4 USD | -0.03 | -12 | -121 | -11 | -65 USD | 32 % |
| a favor del color de la vela | 131 | 51 % | -21 USD | -0.16 | -11 | -103 | -10 | -59 USD | 37 % |


### +20 / cobertura a −10 (= pérdida fija de 10)

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 97 | 37 % | +69 USD | +0.72 | -11 | -113 | -10 | -53 USD | 22 % |
| a favor del color de la vela | 100 | 34 % | -21 USD | -0.21 | -11 | -197 | -10 | -63 USD | 39 % |


### +10 sin cobertura, hasta 4 horas

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 129 | 62 % | -153 USD | -1.18 | -77 | -276 | -78 | -198 USD | 38 % |
| a favor del color de la vela | 126 | 63 % | +73 USD | +0.58 | -57 | -87 | -65 | -186 USD | 4 % |


### Promediar: otra 0,01 cada −10 (máx. 3), todo en +10, corte a −40

| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| a favor de la flecha grande (▲/▼) | 150 | 44 % | -191 USD | -1.27 | -92 | -429 | -92 | -195 USD | 49 % |
| a favor del color de la vela | 134 | 46 % | +127 USD | +0.95 | -92 | -241 | -92 | -179 USD | 4 % |

