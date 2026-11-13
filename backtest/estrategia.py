"""
Simulación de la forma de operar de Claudio con el indicador:

  - Entrada: al cierre de una vela con ▲ o ▼ en 90 % o más (se prueba "a favor"
    de la flecha grande y "a favor" del color de la vela), 0,01 lote, una
    operación (o canasta) a la vez.
  - Salida: con 10 o 20 USD de ganancia.
  - Si va 10 USD en contra se abre "otra": se prueban dos lecturas,
      cobertura opuesta (equivale a fijar la pérdida en -10) y
      promediar a favor (otra 0,01 cada -10, hasta 3, cierre de todo en +10).
  - Variante sin cobertura: esperar el +10 hasta 4 horas.

Cada resultado se compara con lo mismo entrando en velas al azar (misma
cantidad de entradas, dirección al azar), repetido muchas veces.

A 0,01 lote en XAUUSD, 1 USD de movimiento del precio = 1 USD de ganancia o
pérdida. Se descuenta un costo de COSTO USD por posición (spread + comisión).
"""
import asyncio, math, os, random, sys
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import backtest as bt                                     # descarga y cálculo de velas

OUT = bt.OUT
COSTO = float(os.environ.get("COSTO", "0.40"))
MAX_SEG = 5 * 86400                                       # límite de una canasta abierta
RUNS = int(os.environ.get("RUNS", "500"))
CHUNK = 20000


def first_hit(rel, cond_fn, i0, i1):
    """Primer índice en [i0, i1) donde cond_fn(rel[ventana]) es True, recorriendo de a bloques."""
    i = i0
    while i < i1:
        j = min(i + CHUNK, i1)
        m = cond_fn(rel(i, j))
        if m.any():
            return i + int(np.argmax(m))
        i = j
    return -1


class Sim:
    def __init__(self, t, p):
        self.t, self.p = t, p

    def entry_index(self, candle_t):
        return int(np.searchsorted(self.t, candle_t + bt.BAR))        # primer precio de la vela siguiente

    def end_index(self, i0, seconds):
        return int(np.searchsorted(self.t, self.t[i0] + seconds))

    def tp_sl(self, i0, d, tp, sl, seconds):
        """Una posición: cierra en +tp, en -sl (si sl) o al vencer el tiempo."""
        p, e = self.p, self.p[i0]
        i1 = min(self.end_index(i0, seconds), len(p))
        rel = lambda a, b: d * (p[a:b] - e)
        cond = (lambda r: (r >= tp) | (r <= -sl)) if sl else (lambda r: r >= tp)
        k = first_hit(rel, cond, i0, i1)
        k = k if k >= 0 else i1 - 1
        mae = float(min(0.0, (d * (p[i0:k + 1] - e)).min()))
        return d * (p[k] - e) - COSTO, k, mae

    def promediar(self, i0, d, tp=10.0, paso=10.0, maximo=3, corte=40.0, seconds=MAX_SEG):
        """Otra 0,01 a favor cada -paso (hasta 'maximo'), cierre de todo en +tp; corte a -corte del primer precio."""
        p, e0 = self.p, self.p[i0]
        iend = min(self.end_index(i0, seconds), len(p))
        entries, i, mae = [e0], i0, 0.0
        while True:
            k = len(entries)
            # precio que hace que la canasta llegue a +tp, nivel de la próxima entrada y corte
            target = (tp + COSTO * k) / k + sum(entries) / k
            nxt = e0 - d * paso * k if k < maximo else None
            stop = e0 - d * corte
            def cond(r, target=target, nxt=nxt):
                c = (d * (r - target) >= 0) | (d * (r - stop) <= 0)
                if nxt is not None:
                    c |= d * (r - nxt) <= 0
                return c
            j = first_hit(lambda a, b: p[a:b], cond, i, iend)
            seg_end = j if j >= 0 else iend - 1
            seg = p[i:seg_end + 1]
            mae = min(mae, float(sum(d * (seg.min() if d > 0 else seg.max()) - d * x for x in entries)) - COSTO * k)
            if j < 0:                                     # venció el tiempo
                return float(sum(d * (p[seg_end] - x) for x in entries)) - COSTO * k, seg_end, mae
            price = p[j]
            if d * (price - target) >= 0 or d * (price - stop) <= 0:
                return float(sum(d * (price - x) for x in entries)) - COSTO * k, j, mae
            entries.append(price); i = j + 1


STRATS = [
    ("+10 / cobertura a −10 (= pérdida fija de 10)", lambda s, i, d: s.tp_sl(i, d, 10, 10, MAX_SEG)),
    ("+20 / cobertura a −10 (= pérdida fija de 10)", lambda s, i, d: s.tp_sl(i, d, 20, 10, MAX_SEG)),
    ("+10 sin cobertura, hasta 4 horas", lambda s, i, d: s.tp_sl(i, d, 10, None, 4 * 3600)),
    ("Promediar: otra 0,01 cada −10 (máx. 3), todo en +10, corte a −40", lambda s, i, d: s.promediar(i, d)),
]


def run_source(name, ticks, candles):
    t = np.array([x[0] for x in ticks], dtype=float)
    p = np.array([x[1] for x in ticks], dtype=float)
    sim = Sim(t, p)
    usable = [c for c in candles if sim.entry_index(c["t"]) < len(t) - 1]
    big = lambda c: max(c["up"], c["down"])
    rules = [
        ("a favor de la flecha grande (▲/▼)", lambda c: (1 if c["up"] >= c["down"] else -1) if big(c) >= 90 else 0),
        ("a favor del color de la vela", lambda c: (1 if c["color"] == "up" else -1 if c["color"] == "down" else 0) if big(c) >= 90 else 0),
    ]
    out = [f"## {name}", "",
           f"{len(usable)} velas M15 · costo por posición {COSTO:.2f} USD · una canasta a la vez · comparación con {RUNS} pruebas de entradas al azar", ""]
    for sname, fn in STRATS:
        # resultado de entrar en cada vela, en cada dirección
        res = {}
        for c in usable:
            i0 = sim.entry_index(c["t"])
            for d in (1, -1):
                pnl, k, mae = fn(sim, i0, d)
                res[(c["t"], d)] = (pnl, float(t[k]), mae)
        out += [f"### {sname}", "",
                "| Entrada | Operaciones | Ganadoras | Resultado total | Promedio | Peor operación | Peor racha (caída de saldo) | Peor flotante | Azar: resultado típico | Entradas al azar con resultado igual o mejor |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for rname, rule in rules:
            trades = take(usable, lambda c: rule(c), res)
            sig_total = sum(x[0] for x in trades)
            n_sig = sum(1 for c in usable if rule(c) != 0)
            q = n_sig / len(usable) if usable else 0
            rnd = []
            for k in range(RUNS):
                rng = random.Random(k)
                pick = lambda c, rng=rng: (rng.choice((1, -1)) if rng.random() < q else 0)
                rnd.append(sum(x[0] for x in take(usable, pick, res)))
            better = sum(1 for v in rnd if v >= sig_total) / len(rnd) if rnd else float("nan")
            out.append(row(rname, trades, sig_total, better, sorted(rnd)[len(rnd) // 2] if rnd else float('nan')))
        out += ["", ""]
    return "\n".join(out)


def take(candles, rule, res):
    trades, busy = [], -1.0
    for c in candles:
        d = rule(c)
        if d == 0 or c["t"] + bt.BAR < busy:
            continue
        pnl, exit_t, mae = res[(c["t"], d)]
        trades.append((pnl, mae)); busy = exit_t
    return trades


def row(name, trades, total, better, med):
    if not trades:
        return f"| {name} | 0 | — | — | — | — | — | — | — | — |"
    eq, peak, dd = 0.0, 0.0, 0.0
    for pnl, _ in trades:
        eq += pnl; peak = max(peak, eq); dd = min(dd, eq - peak)
    wins = sum(1 for pnl, _ in trades if pnl > 0)
    return (f"| {name} | {len(trades)} | {wins * 100 / len(trades):.0f} % | {total:+.0f} USD | {total / len(trades):+.2f} | "
            f"{min(x[0] for x in trades):+.0f} | {dd:.0f} | {min(x[1] for x in trades):.0f} | {med:+.0f} USD | {better * 100:.0f} % |")


def main():
    os.makedirs(OUT, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [f"# Simulación de la estrategia · velas M15 · últimos {bt.DAYS} días", "", f"Generado: {now}", "",
          "Lote 0,01 (1 USD de precio = 1 USD de resultado). Se entra en el primer precio de la vela siguiente a la señal. "
          "Una cobertura opuesta del mismo tamaño congela la pérdida en ese punto, así que se simula como un cierre a −10 "
          "(en la realidad cuesta además otro spread y el swap mientras está abierta). "
          "**Peor flotante** es la peor pérdida no realizada que tuvo una operación antes de cerrar. "
          "**Entradas al azar con resultado igual o mejor**: si es alto (por ejemplo, más de 10–20 %), la señal no le gana al azar.", ""]
    try:
        dt = asyncio.run(bt.deriv_ticks())
        md.append(run_source("Deriv · frxXAUUSD", dt, bt.candles_from(dt, False, 200)))
    except Exception as e:
        md.append(f"## Deriv\n\nError: `{e!r}`\n")
    try:
        bn = bt.binance_trades()
        md.append(run_source("Binance Futuros · XAUUSDT (volumen negociado)", bn, bt.candles_from(bn, True, 50)))
    except Exception as e:
        md.append(f"## Binance\n\nError: `{e!r}`\n")
    text = "\n".join(md)
    with open(f"{OUT}/estrategia.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
