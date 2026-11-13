# Volumen XAUUSD

Página web de un solo archivo que muestra el **perfil de volumen por vela** del oro (XAUUSD) y el **porcentaje del máximo volumen**, con el mismo cálculo que usa [va-mod.ru](https://va-mod.ru/), pero sin depender de ese sitio.

No necesita instalación, servidor ni cuentas: es un `index.html` que se conecta directo a las fuentes de datos públicas desde el navegador.

## Cómo usarla

- **En tu compu:** descargá `index.html` y abrilo con doble clic (Chrome, Edge o Firefox).
- **Online con GitHub Pages:** en el repo, *Settings → Pages → Branch: `main` / root → Save*. Queda en `https://<usuario>.github.io/volumen-xauusd/`. En un repo privado, GitHub Pages requiere un plan pago.

La configuración elegida (fuente, temporalidad, cantidad de velas, redondeo y alertas) se guarda en el navegador.

## Fuentes de datos

| Fuente | Instrumento | Qué es el "volumen" | Horario | Notas |
|---|---|---|---|---|
| **Deriv** | `frxXAUUSD` | Cantidad de ticks (≈1 por segundo) | Horario forex, cerrado el fin de semana | La misma fuente que usa va-mod.ru. |
| **Binance Futuros** (por defecto) | `XAUUSDT` (perpetuo TradFi) | Volumen negociado real, en onzas, o cantidad de operaciones | 24/7 | Historial rápido. Binance no está disponible desde EE. UU. |
| **OKX** | `XAU-USDT-SWAP` (perpetuo) | Volumen negociado real, en contratos de 0,001 oz, o cantidad de operaciones | 24/7 | Paso de precio de 0,1. El historial tarda más en cargar (de a 100 operaciones por pedido). |

Si una fuente deja de funcionar, se elige otra desde el selector **Fuente**. Ninguna requiere clave.

Diferencias a tener en cuenta:

- Binance y OKX son contratos perpetuos que cotizan en USDT. El precio suele diferir unos dólares del XAUUSD de un broker de CFD, pero el porcentaje es relativo al rango de cada vela, así que lo que importa es la forma del perfil.
- Con Binance u OKX el resultado puede no coincidir con va-mod.ru, porque el volumen sale de operaciones reales y no de ticks de cotización.

## Cómo se calcula el porcentaje

Para cada vela:

1. Se suma el volumen de cada precio (ticks, operaciones o volumen negociado, según la fuente y la opción elegida).
2. El precio con más volumen es el **máximo volumen** de la vela.
3. Los niveles de precio se ordenan de mayor a menor y se mira en qué posición quedó el máximo volumen: `posición × 100 / cantidad de niveles`, redondeado.
4. Si la vela es alcista se muestra ese valor con ⬈. Si es bajista se muestra `100 − valor` con ⬊. Si da 50, o la vela no tiene cuerpo, se muestra ⬍.
5. El color compara el máximo volumen con el último precio de la vela: **verde** si el máximo volumen está por debajo del precio, **rojo** si está por encima.

En las tarjetas superiores, ▲ y ▼ son ese porcentaje y su complemento, para la vela anterior (cerrada) y la vela en curso.

Con la fuente Deriv, en vivo solo se cuenta un tick cuando cambia el precio, igual que va-mod.ru. La opción *Contar ticks repetidos en vivo* cuenta todos.

## Alertas sonoras

En la barra **Alertas**, debajo de los controles:

- **Antes del cierre:** suenan tres pitidos agudos si, en los últimos segundos de la vela en curso (10 por defecto), ▲ o ▼ llega al umbral (90 % por defecto). Suena una sola vez por vela, la primera vez que se cumple dentro de esa ventana.
- **Al cierre:** suena una campana de dos notas si la vela que acaba de cerrar quedó con ▲ o ▼ en el umbral o más. Se evalúa 1,5 s después del cierre, para que lleguen las últimas operaciones.

Los botones ▶ prueban cada sonido. El navegador solo habilita el audio después de un clic en la página: si la abrís y no la tocás, no suena. Las alertas siguen funcionando con la pestaña en segundo plano, pero no con el navegador cerrado ni con la compu suspendida.

## Limitaciones

- El "volumen" de Deriv no es volumen real: es la cantidad de veces que el broker publicó cada precio.
- La página depende de que las APIs públicas de Deriv, Binance y OKX sigan abiertas y con el mismo formato.
- El historial se descarga al abrir la página o al cambiar un ajuste. Con muchas velas o temporalidades altas puede tardar.
- Es una herramienta de análisis, no una señal de trading.
