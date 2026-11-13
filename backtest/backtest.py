"""
Prueba histórica del indicador de volumen de va-mod.ru y del patrón P/b/D.

Descarga ticks de Deriv (frxXAUUSD) y, si están disponibles, operaciones de
Binance Futuros (XAUUSDT, archivos diarios de data.binance.vision); arma velas
M15 con su perfil de volumen por precio, calcula exactamente lo mismo que la
página (porcentaje ▲/▼ y patrón) y mide qué hizo la vela siguiente.

Uso:  python backtest/backtest.py            (variables: DAYS, BAR, OUT)
"""
import asyncio, io, json, math, os, sys, time, zipfile, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

DAYS = int(os.environ.get("DAYS", "21"))
BAR = int(os.environ.get("BAR", "900"))
OUT = os.environ.get("OUT", "backtest/resultados")
NOW = int(time.time())
START = NOW - DAYS * 86400

DERIV_URLS = ["wss://api.derivws.com/trading/v1/options/ws/public",
              "wss://ws.derivws.com/websockets/v3?app_id=1089"]


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- Deriv
async def deriv_ticks():
    import websockets
    last_err = None
    for url in DERIV_URLS:
        try:
            return await _deriv_from(url)
        except Exception as e:                     # probar la otra dirección
            last_err = e
            log(f"Deriv: falló {url}: {e!r}")
    raise RuntimeError(f"Deriv no respondió: {last_err!r}")


async def _deriv_from(url):
    import websockets
    ticks = {}
    end, calls, req = NOW, 0, 0
    async with websockets.connect(url, max_size=2**24, open_timeout=20, ping_interval=20) as ws:
        while end > START and calls < 20000:
            req += 1
            await ws.send(json.dumps({"ticks_history": "frxXAUUSD", "style": "ticks",
                                      "start": end - 3600, "end": end, "count": 1000, "req_id": req}))
            d = json.loads(await asyncio.wait_for(ws.recv(), 60))
            calls += 1
            if "error" in d:
                code = d["error"].get("code", "")
                if code in ("RateLimit", "TooManyRequests"):
                    await asyncio.sleep(5); continue
                end -= 3600; continue                  # hora sin datos (fin de semana, pausa diaria)
            times, prices = d["history"]["times"], d["history"]["prices"]
            for t, p in zip(times, prices):
                ticks[int(t)] = float(p)
            if len(times) < 1000:
                end = end - 3600                       # la hora entera ya está leída
            else:
                end = min(times) - 1
            if calls % 100 == 0:
                log(f"Deriv: {calls} pedidos, {len(ticks)} ticks, hasta {datetime.fromtimestamp(end, timezone.utc):%Y-%m-%d %H:%M} UTC")
    log(f"Deriv: listo, {len(ticks)} ticks en {calls} pedidos")
    return [(t, p, 1.0) for t, p in sorted(ticks.items()) if t >= START]


# ---------------------------------------------------------------- Binance
def binance_trades():
    out = []
    day = datetime.fromtimestamp(START, timezone.utc).date()
    last = datetime.fromtimestamp(NOW, timezone.utc).date()
    while day <= last:
        url = f"https://data.binance.vision/data/futures/um/daily/aggTrades/XAUUSDT/XAUUSDT-aggTrades-{day:%Y-%m-%d}.zip"
        try:
            raw = urllib.request.urlopen(url, timeout=120).read()
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                data = z.read(z.namelist()[0]).decode()
            n0 = len(out)
            for line in data.splitlines():
                f = line.split(",")
                if not f or not f[0].strip().isdigit():
                    continue                            # encabezado
                # agg_trade_id, price, quantity, first_trade_id, last_trade_id, transact_time, is_buyer_maker
                t = int(f[5]) / 1000.0
                if START <= t <= NOW:
                    out.append((t, float(f[1]), float(f[2])))
            log(f"Binance {day}: {len(out) - n0} operaciones")
        except Exception as e:
            log(f"Binance {day}: sin archivo ({e.__class__.__name__})")
        day += timedelta(days=1)
    out.sort()
    return out


# ---------------------------------------------------------------- velas y cálculo (igual que la página)
def candles_from(ticks, weight_volume, min_n):
    cs = {}
    for t, p, q in ticks:
        b = int(t // BAR) * BAR
        c = cs.get(b)
        if c is None:
            c = cs[b] = {"t": b, "o": p, "h": p, "l": p, "c": p, "n": 0, "lv": defaultdict(float)}
        c["h"] = max(c["h"], p); c["l"] = min(c["l"], p); c["c"] = p; c["n"] += 1
        c["lv"][p] += q if weight_volume else 1.0
    out = []
    for b in sorted(cs):
        c = cs[b]
        if c["n"] < min_n:
            continue
        lv = sorted(c["lv"].items(), key=lambda x: -x[0])        # de mayor a menor precio
        mx, idx = 0.0, 0
        for i, (_, v) in enumerate(lv):
            if v >= mx:                                           # igual que la página: el último empate
                mx, idx = v, i
        c.update(nl=len(lv), poc=lv[idx][0], idx=idx)
        del c["lv"]
        out.append(enrich(c))
    return out


def jsround(x):
    return int(math.floor(x + 0.5))


def enrich(c):
    color = "up" if c["c"] > c["o"] else "down" if c["c"] < c["o"] else "flat"
    pct = jsround(c["idx"] * 100 / c["nl"])
    if color == "down":
        d = "0" if pct == 50 else "down"; pct = 100 - pct
    elif color == "up":
        d = "0" if pct == 50 else "up"
    else:
        d = "0"
    if d == "up":   up, down = pct, 100 - pct
    elif d == "down": up, down = 100 - pct, pct
    else:            up, down = pct, pct
    pos = c["idx"] / (c["nl"] - 1) if c["nl"] > 1 else 0.5
    shape = "P" if pos < 1 / 3 else "b" if pos > 2 / 3 else "D"
    side = "none" if shape == "D" else ("buy" if c["c"] > c["poc"] else "sell" if c["c"] < c["poc"] else "none")
    verdict = "" if side == "none" or color == "flat" else ("Bien" if (side == "buy") == (color == "up") else "Cuidado")
    c.update(color=color, up=up, down=down, shape=shape, side=side, verdict=verdict)
    return c


def evaluate(cs):
    pairs = []
    for i in range(len(cs) - 1):
        if cs[i + 1]["t"] - cs[i]["t"] != BAR:
            continue
        four = cs[i + 4] if i + 4 < len(cs) and cs[i + 4]["t"] - cs[i]["t"] == 4 * BAR else None
        pairs.append((cs[i], cs[i + 1], four))

    big = lambda a: max(a["up"], a["down"])
    big_side = lambda a: 1 if a["up"] >= a["down"] else -1
    pat_side = lambda a: 1 if a["side"] == "buy" else -1 if a["side"] == "sell" else 0
    col_side = lambda a: 1 if a["color"] == "up" else -1 if a["color"] == "down" else 0

    def stat(name, filt, pred):
        n = hit = 0; mv = mv4 = 0.0; n4 = 0
        for a, b, d in pairs:
            if not filt(a):
                continue
            p = pred(a)
            nd = 1 if b["c"] > b["o"] else -1 if b["c"] < b["o"] else 0
            if p == 0 or nd == 0:
                continue
            n += 1; hit += nd == p; mv += p * (b["c"] - a["c"])
            if d:
                n4 += 1; mv4 += p * (d["c"] - a["c"])
        r = hit / n if n else float("nan")
        se = math.sqrt(0.25 / n) if n else float("nan")
        z = (r - 0.5) / se if n else float("nan")
        pval = math.erfc(abs(z) / math.sqrt(2)) if n else float("nan")
        return {"lectura": name, "casos": n, "acierto": r, "ic95": (r - 1.96 * se, r + 1.96 * se) if n else None,
                "p": pval, "usd_1": mv / n if n else float("nan"), "usd_4": mv4 / n4 if n4 else float("nan")}

    res = [
        stat("Referencia: la vela siguiente repite el color", lambda a: True, col_side),
        stat("Flecha ≥90 %: hacia el lado mayor", lambda a: big(a) >= 90, big_side),
        stat("Flecha ≥80 %: hacia el lado mayor", lambda a: big(a) >= 80, big_side),
        stat("Flecha ≥90 %: al revés del lado mayor", lambda a: big(a) >= 90, lambda a: -big_side(a)),
        stat("Patrón con señal (P o b): compra/venta", lambda a: a["side"] != "none", pat_side),
        stat("Patrón P", lambda a: a["shape"] == "P" and a["side"] != "none", pat_side),
        stat("Patrón b", lambda a: a["shape"] == "b" and a["side"] != "none", pat_side),
        stat("Patrón «Bien» (continuación)", lambda a: a["verdict"] == "Bien", pat_side),
        stat("Patrón «Cuidado» (giro)", lambda a: a["verdict"] == "Cuidado", pat_side),
        stat("Flecha ≥90 % y patrón con señal: sigue el patrón", lambda a: big(a) >= 90 and a["side"] != "none", pat_side),
        stat("Flecha ≥90 % y patrón en la misma dirección", lambda a: big(a) >= 90 and a["side"] != "none" and pat_side(a) == big_side(a), pat_side),
    ]
    ups = sum(1 for _, b, _ in pairs if b["c"] > b["o"])
    info = {"velas": len(cs), "pares": len(pairs), "sube_pct": ups / len(pairs) if pairs else float("nan"),
            "desde": datetime.fromtimestamp(cs[0]["t"], timezone.utc).isoformat() if cs else None,
            "hasta": datetime.fromtimestamp(cs[-1]["t"], timezone.utc).isoformat() if cs else None,
            "rango_medio_usd": sum(c["h"] - c["l"] for c in cs) / len(cs) if cs else float("nan"),
            "formas": {k: sum(1 for c in cs if c["shape"] == k) for k in "PbD"},
            "flecha_90": sum(1 for c in cs if big(c) >= 90)}
    return info, res


# ---------------------------------------------------------------- informe
def fmt_pct(x):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:.1f} %"


def table(info, res):
    lines = [f"- Velas M15: **{info['velas']}** ({info['desde'][:10]} a {info['hasta'][:10]}), pares consecutivos: {info['pares']}",
             f"- Velas siguientes alcistas: {fmt_pct(info['sube_pct'])} · rango medio de una vela: {info['rango_medio_usd']:.2f} USD",
             f"- Formas: P {info['formas']['P']}, b {info['formas']['b']}, D {info['formas']['D']} · velas con flecha ≥90 %: {info['flecha_90']}",
             "",
             "| Lectura | Casos | Acierto vela siguiente | IC 95 % | p | USD a favor, 1 vela | USD a favor, 4 velas |",
             "|---|---:|---:|---|---:|---:|---:|"]
    for r in res:
        ic = f"{r['ic95'][0] * 100:.0f}–{r['ic95'][1] * 100:.0f} %" if r["ic95"] else "—"
        p = "—" if math.isnan(r["p"]) else f"{r['p']:.3f}"
        u1 = "—" if math.isnan(r["usd_1"]) else f"{r['usd_1']:+.2f}"
        u4 = "—" if math.isnan(r["usd_4"]) else f"{r['usd_4']:+.2f}"
        lines.append(f"| {r['lectura']} | {r['casos']} | {fmt_pct(r['acierto'])} | {ic} | {p} | {u1} | {u4} |")
    return "\n".join(lines)


def main():
    os.makedirs(OUT, exist_ok=True)
    sections, raw = [], {}
    try:
        dt = asyncio.run(deriv_ticks())
        cs = candles_from(dt, False, 200)
        info, res = evaluate(cs)
        raw["deriv"] = {"info": info, "res": res}
        sections.append(("Deriv · frxXAUUSD · volumen = cantidad de ticks (como va-mod.ru)", table(info, res)))
        write_csv(f"{OUT}/velas_deriv.csv", cs)
    except Exception as e:
        sections.append(("Deriv", f"No se pudieron bajar los datos: `{e!r}`"))
    try:
        bt = binance_trades()
        if bt:
            for weighted, label, key in ((True, "volumen negociado", "binance_vol"), (False, "cantidad de operaciones", "binance_ops")):
                cs = candles_from(bt, weighted, 50)
                info, res = evaluate(cs)
                raw[key] = {"info": info, "res": res}
                sections.append((f"Binance Futuros · XAUUSDT · medido por {label}", table(info, res)))
                write_csv(f"{OUT}/velas_{key}.csv", cs)
        else:
            sections.append(("Binance Futuros", "No se pudieron bajar los archivos diarios."))
    except Exception as e:
        sections.append(("Binance Futuros", f"No se pudieron bajar los datos: `{e!r}`"))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [f"# Prueba histórica · velas M15 · últimos {DAYS} días", "", f"Generado: {now}", "",
          "Cada fila toma las velas que cumplen la lectura y mira la vela siguiente: **acierto** es el porcentaje de veces que fue para el lado indicado (el azar da 50 %). "
          "**IC 95 %** es el margen de error: si incluye el 50 %, no se distingue del azar. **p** chico (menos de 0,05) indicaría algo más que suerte, "
          "aunque con muchas filas alguna puede salir baja por casualidad. **USD a favor** es cuánto se movió el cierre en la dirección indicada, en promedio, sin descontar spread ni comisiones.", ""]
    for title, body in sections:
        md += [f"## {title}", "", body, ""]
    with open(f"{OUT}/resultados.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    with open(f"{OUT}/resultados.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1, default=str)
    log("\n".join(md))


def write_csv(path, cs):
    cols = ["t", "o", "h", "l", "c", "n", "nl", "poc", "idx", "up", "down", "shape", "side", "verdict"]
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for c in cs:
            f.write(",".join(str(c[k]) for k in cols) + "\n")


if __name__ == "__main__":
    main()
