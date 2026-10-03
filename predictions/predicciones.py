import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf


# ============================================================
# UTILIDADES
# ============================================================

def leer_float(mensaje: str, default: float) -> float:
    texto = input(mensaje).strip()
    if not texto:
        return default
    return float(texto)


def leer_int(mensaje: str, default: int) -> int:
    texto = input(mensaje).strip()
    if not texto:
        return default
    return int(texto)


def leer_texto(mensaje: str, default: str = "") -> str:
    texto = input(mensaje).strip()
    return texto if texto else default


def siguiente_jueves_14(base_dt: datetime) -> datetime:
    """
    Calcula el próximo jueves a las 14:00, en la misma zona horaria de base_dt.
    Python: Monday=0 ... Thursday=3
    """
    dias_hasta_jueves = (3 - base_dt.weekday()) % 7

    # Si hoy es jueves y ya pasó las 14:00, va al próximo jueves
    if dias_hasta_jueves == 0 and (base_dt.hour > 14 or (base_dt.hour == 14 and base_dt.minute > 0)):
        dias_hasta_jueves = 7

    objetivo = (base_dt + timedelta(days=dias_hasta_jueves)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    return objetivo


def convertir_a_timestamp_tz(texto_fecha: str, timezone_str: str) -> pd.Timestamp:
    """
    Convierte 'YYYY-MM-DD HH:MM' a Timestamp con zona horaria.
    """
    dt_naive = datetime.strptime(texto_fecha, "%Y-%m-%d %H:%M")
    dt_aware = dt_naive.replace(tzinfo=ZoneInfo(timezone_str))
    return pd.Timestamp(dt_aware)


def formatear_moneda(x: float) -> str:
    return f"${x:,.2f}"


# ============================================================
# DESCARGA Y SELECCIÓN DE PRECIOS
# ============================================================

def descargar_intradia(
    ticker: str,
    start: datetime,
    end: datetime,
    interval: str = "30m",
    prepost: bool = True
) -> pd.DataFrame:
    """
    Descarga datos intradía desde Yahoo Finance.
    """
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        prepost=prepost,
        progress=False,
        threads=False
    )

    if df.empty:
        raise ValueError(f"No se encontraron datos intradía para '{ticker}'.")

    # A veces yfinance devuelve MultiIndex aunque sea un ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(how="all")

    if df.empty:
        raise ValueError(f"Los datos descargados para '{ticker}' están vacíos después de limpiar NA.")

    return df


def descargar_historico(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Descarga histórico diario para análisis simple.
    """
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=False
    )

    if df.empty:
        raise ValueError(f"No se encontraron datos históricos para '{ticker}'.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(how="all")
    return df


def obtener_punto_mas_cercano(
    df: pd.DataFrame,
    objetivo: pd.Timestamp,
    max_diferencia_minutos: int = 120
) -> dict:
    """
    Busca la vela/registro más cercano al momento objetivo.
    """
    if df.empty:
        raise ValueError("DataFrame vacío.")

    indice = df.index.get_indexer([objetivo], method="nearest")[0]
    if indice == -1:
        raise ValueError("No se pudo encontrar un punto cercano al tiempo objetivo.")

    ts_real = df.index[indice]
    fila = df.iloc[indice]

    diferencia = abs((ts_real - objetivo).total_seconds()) / 60.0
    if diferencia > max_diferencia_minutos:
        raise ValueError(
            f"No hay un dato suficientemente cercano al tiempo objetivo. "
            f"Diferencia encontrada: {diferencia:.1f} minutos."
        )

    return {
        "timestamp_real": ts_real.isoformat(),
        "close": float(fila["Close"]),
        "open": float(fila["Open"]) if "Open" in df.columns else None,
        "high": float(fila["High"]) if "High" in df.columns else None,
        "low": float(fila["Low"]) if "Low" in df.columns else None,
        "volume": float(fila["Volume"]) if "Volume" in df.columns else None,
        "diferencia_minutos": round(diferencia, 2)
    }


# ============================================================
# ANÁLISIS SIMPLE
# ============================================================

def prediccion_lineal(close: pd.Series, horizon: int = 5, lookback: int = 20) -> pd.DataFrame:
    """
    Predicción muy simple por regresión lineal usando numpy.polyfit.
    Sirve como apoyo, no como modelo financiero serio.
    """
    if len(close) < 10:
        raise ValueError("Muy pocos datos para hacer una predicción lineal.")

    lookback = min(lookback, len(close))
    y = close.tail(lookback).astype(float).values
    x = np.arange(len(y), dtype=float)

    m, b = np.polyfit(x, y, 1)

    x_future = np.arange(len(y), len(y) + horizon, dtype=float)
    y_future = m * x_future + b
    y_future = np.maximum(y_future, 0.01)

    future_index = pd.bdate_range(
        start=close.index[-1] + pd.Timedelta(days=1),
        periods=horizon
    )

    return pd.DataFrame({"Predicted_Close": y_future}, index=future_index)


def analisis_basico_ticker(ticker: str) -> dict:
    """
    Saca algunas métricas sencillas para justificar la elección.
    """
    df = descargar_historico(ticker, period="3mo", interval="1d")

    close = df["Close"].copy()
    ma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else np.nan

    retorno_5d = ((close.iloc[-1] / close.iloc[-6]) - 1) * 100 if len(close) >= 6 else np.nan
    retorno_20d = ((close.iloc[-1] / close.iloc[-21]) - 1) * 100 if len(close) >= 21 else np.nan

    volatilidad = close.pct_change().dropna().std() * np.sqrt(252) * 100 if len(close) > 2 else np.nan

    pred = prediccion_lineal(close, horizon=5, lookback=min(20, len(close)))
    esperado_5d = ((pred["Predicted_Close"].iloc[-1] / close.iloc[-1]) - 1) * 100

    return {
        "ultimo_cierre": float(close.iloc[-1]),
        "ma20": float(ma20) if pd.notna(ma20) else None,
        "retorno_5d_pct": float(retorno_5d) if pd.notna(retorno_5d) else None,
        "retorno_20d_pct": float(retorno_20d) if pd.notna(retorno_20d) else None,
        "volatilidad_anualizada_pct": float(volatilidad) if pd.notna(volatilidad) else None,
        "prediccion_lineal_5d_pct": float(esperado_5d)
    }


# ============================================================
# REPORTES
# ============================================================

def construir_reporte_inicial(snapshot: dict) -> str:
    lineas = []
    lineas.append("SHORT REPORT")
    lineas.append("=" * 60)
    lineas.append("")
    lineas.append("PART 1: INVESTMENT")
    lineas.append("-" * 60)
    lineas.append(f"Chosen company: {snapshot['company_name']} ({snapshot['ticker']})")
    lineas.append(f"Investment amount: {formatear_moneda(snapshot['investment_amount'])}")
    lineas.append(f"Target buy time: {snapshot['buy_target']}")
    lineas.append(f"Nearest market timestamp used: {snapshot['buy_executed']['timestamp_real']}")
    lineas.append(f"Buy price used: {formatear_moneda(snapshot['buy_executed']['close'])}")
    lineas.append(f"Expected evaluation time: {snapshot['evaluation_target']}")
    lineas.append("")

    analisis = snapshot["market_analysis"]
    lineas.append("Yahoo Finance support analysis:")
    lineas.append(f"- Last close: {formatear_moneda(analisis['ultimo_cierre'])}")
    lineas.append(f"- 20-day moving average: {formatear_moneda(analisis['ma20']) if analisis['ma20'] is not None else 'N/A'}")
    lineas.append(f"- 5-day return: {analisis['retorno_5d_pct']:.2f}%"
                  if analisis['retorno_5d_pct'] is not None else "- 5-day return: N/A")
    lineas.append(f"- 20-day return: {analisis['retorno_20d_pct']:.2f}%"
                  if analisis['retorno_20d_pct'] is not None else "- 20-day return: N/A")
    lineas.append(f"- Annualized volatility (simple estimate): {analisis['volatilidad_anualizada_pct']:.2f}%"
                  if analisis['volatilidad_anualizada_pct'] is not None else "- Annualized volatility: N/A")
    lineas.append(f"- Expected profit from simple linear trend (5 business days): {analisis['prediccion_lineal_5d_pct']:.2f}%")
    lineas.append("")
    lineas.append(f"Brief rationale: {snapshot['final_rationale']}")
    lineas.append("")

    lineas.append("PART 2: PROMPTS")
    lineas.append("-" * 60)
    for i, rec in enumerate(snapshot["models_evaluated"], start=1):
        lineas.append(f"Model {i}: {rec['model_name']}")
        lineas.append(f"Prompt: {rec['prompt']}")
        lineas.append(f"Recommended ticker/company: {rec['recommended_ticker']} / {rec['recommended_company']}")
        lineas.append(f"Expected profit (%): {rec['expected_profit_pct']}")
        lineas.append(f"Reasoning summary: {rec['reasoning_summary']}")
        lineas.append("")

    lineas.append("Evaluation status: Pending until the target evaluation time.")
    return "\n".join(lineas)


def construir_reporte_final(snapshot: dict, resultado: dict) -> str:
    texto = construir_reporte_inicial(snapshot)
    extra = []
    extra.append("")
    extra.append("FINAL EVALUATION")
    extra.append("-" * 60)
    extra.append(f"Target evaluation time: {snapshot['evaluation_target']}")
    extra.append(f"Nearest market timestamp used: {resultado['sell_executed']['timestamp_real']}")
    extra.append(f"Sell/measurement price used: {formatear_moneda(resultado['sell_executed']['close'])}")
    extra.append(f"Shares purchased: {resultado['shares']:.6f}")
    extra.append(f"Final portfolio value: {formatear_moneda(resultado['final_value'])}")
    extra.append(f"Profit/Loss: {formatear_moneda(resultado['profit'])}")
    extra.append(f"Return: {resultado['return_pct']:.2f}%")
    return texto + "\n" + "\n".join(extra)


# ============================================================
# GRÁFICAS
# ============================================================

def graficar_experimento(
    ticker: str,
    buy_dt: pd.Timestamp,
    eval_dt: pd.Timestamp,
    buy_price: float,
    sell_price: float | None = None
) -> None:
    inicio = (buy_dt - pd.Timedelta(days=3)).to_pydatetime()
    fin = (eval_dt + pd.Timedelta(days=1)).to_pydatetime()

    df = descargar_intradia(ticker, inicio, fin, interval="30m", prepost=True)

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["Close"], label="Close intradía")

    plt.scatter([buy_dt], [buy_price], marker="o", s=70, label="Compra / medición inicial")
    if sell_price is not None:
        plt.scatter([eval_dt], [sell_price], marker="x", s=90, label="Evaluación final")

    plt.title(f"{ticker.upper()} - Experimento de inversión")
    plt.xlabel("Fecha y hora")
    plt.ylabel("Precio")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


# ============================================================
# MODO 1: PLAN / REGISTRO INICIAL
# ============================================================

def modo_plan() -> None:
    print("\n=== MODO PLAN / REGISTRO INICIAL ===\n")

    timezone_str = leer_texto("Zona horaria [America/New_York]: ", "America/New_York")
    ahora = datetime.now(ZoneInfo(timezone_str))

    default_buy = ahora.replace(hour=17, minute=0, second=0, microsecond=0)
    default_eval = siguiente_jueves_14(ahora)

    print("Registre los modelos generativos que evaluó.\n")
    n_modelos = leer_int("¿Cuántos modelos quiere registrar? [2]: ", 2)

    modelos = []
    for i in range(1, n_modelos + 1):
        print(f"\n--- Modelo {i} ---")
        model_name = leer_texto("Nombre del modelo (ej. ChatGPT, DeepSeek): ")
        prompt = leer_texto("Prompt usado: ")
        recommended_ticker = leer_texto("Ticker recomendado: ").upper()
        recommended_company = leer_texto("Compañía recomendada: ")
        expected_profit_pct = leer_texto("Ganancia esperada (%) según ese modelo: ")
        reasoning_summary = leer_texto("Resumen corto de la recomendación: ")

        modelos.append({
            "model_name": model_name,
            "prompt": prompt,
            "recommended_ticker": recommended_ticker,
            "recommended_company": recommended_company,
            "expected_profit_pct": expected_profit_pct,
            "reasoning_summary": reasoning_summary
        })

    print("\n--- Decisión final ---")
    ticker = leer_texto("Ticker elegido final: ").upper()
    company_name = leer_texto("Nombre de la compañía: ")
    amount = leer_float("Monto a invertir [15000]: ", 15000.0)

    buy_text = leer_texto(
        f"Fecha/hora de compra [YYYY-MM-DD HH:MM] [{default_buy.strftime('%Y-%m-%d %H:%M')}]: ",
        default_buy.strftime("%Y-%m-%d %H:%M")
    )
    eval_text = leer_texto(
        f"Fecha/hora de evaluación [YYYY-MM-DD HH:MM] [{default_eval.strftime('%Y-%m-%d %H:%M')}]: ",
        default_eval.strftime("%Y-%m-%d %H:%M")
    )
    final_rationale = leer_texto("Justificación final de su elección: ")

    buy_target = convertir_a_timestamp_tz(buy_text, timezone_str)
    eval_target = convertir_a_timestamp_tz(eval_text, timezone_str)

    # Descarga alrededor del momento de compra para hallar la vela más cercana
    ventana_inicio = (buy_target - pd.Timedelta(days=3)).to_pydatetime()
    ventana_fin = (buy_target + pd.Timedelta(days=2)).to_pydatetime()

    intradia = descargar_intradia(
        ticker=ticker,
        start=ventana_inicio,
        end=ventana_fin,
        interval="30m",
        prepost=True
    )

    buy_executed = obtener_punto_mas_cercano(intradia, buy_target, max_diferencia_minutos=180)
    market_analysis = analisis_basico_ticker(ticker)

    snapshot = {
        "ticker": ticker,
        "company_name": company_name,
        "investment_amount": amount,
        "timezone": timezone_str,
        "buy_target": buy_target.isoformat(),
        "evaluation_target": eval_target.isoformat(),
        "buy_executed": buy_executed,
        "market_analysis": market_analysis,
        "models_evaluated": modelos,
        "final_rationale": final_rationale
    }

    nombre_base = f"experiment_{ticker.lower()}"
    json_file = Path(f"{nombre_base}_snapshot.json")
    report_file = Path(f"{nombre_base}_report_initial.txt")

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    reporte = construir_reporte_inicial(snapshot)
    report_file.write_text(reporte, encoding="utf-8")

    print("\n===== RESUMEN INICIAL =====")
    print(f"Ticker elegido: {ticker}")
    print(f"Compañía: {company_name}")
    print(f"Monto invertido: {formatear_moneda(amount)}")
    print(f"Precio usado para compra/registro: {formatear_moneda(buy_executed['close'])}")
    print(f"Momento real más cercano encontrado: {buy_executed['timestamp_real']}")
    print(f"Reporte inicial guardado en: {report_file}")
    print(f"Snapshot guardado en: {json_file}")
    print("===========================\n")

    # Gráfica opcional
    ver_grafica = leer_texto("¿Desea ver la gráfica? [s/n] ", "s").lower()
    if ver_grafica == "s":
        graficar_experimento(
            ticker=ticker,
            buy_dt=pd.Timestamp(snapshot["buy_executed"]["timestamp_real"]),
            eval_dt=eval_target,
            buy_price=buy_executed["close"],
            sell_price=None
        )


# ============================================================
# MODO 2: EVALUACIÓN FINAL
# ============================================================

def modo_evaluar() -> None:
    print("\n=== MODO EVALUACIÓN FINAL ===\n")

    snapshot_path = leer_texto("Ruta del snapshot JSON: ")
    if not snapshot_path:
        raise ValueError("Debe indicar la ruta del archivo snapshot JSON.")

    snapshot_file = Path(snapshot_path)
    if not snapshot_file.exists():
        raise FileNotFoundError(f"No existe el archivo: {snapshot_file}")

    with open(snapshot_file, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    ticker = snapshot["ticker"]
    amount = float(snapshot["investment_amount"])
    buy_price = float(snapshot["buy_executed"]["close"])
    eval_target = pd.Timestamp(snapshot["evaluation_target"])

    # Descarga alrededor del momento de evaluación
    ventana_inicio = (eval_target - pd.Timedelta(days=3)).to_pydatetime()
    ventana_fin = (eval_target + pd.Timedelta(days=2)).to_pydatetime()

    intradia = descargar_intradia(
        ticker=ticker,
        start=ventana_inicio,
        end=ventana_fin,
        interval="30m",
        prepost=True
    )

    sell_executed = obtener_punto_mas_cercano(intradia, eval_target, max_diferencia_minutos=180)

    shares = amount / buy_price
    final_value = shares * float(sell_executed["close"])
    profit = final_value - amount
    return_pct = (profit / amount) * 100

    resultado = {
        "sell_executed": sell_executed,
        "shares": shares,
        "final_value": final_value,
        "profit": profit,
        "return_pct": return_pct
    }

    final_report = construir_reporte_final(snapshot, resultado)

    nombre_base = f"experiment_{ticker.lower()}"
    final_report_file = Path(f"{nombre_base}_report_final.txt")
    final_json_file = Path(f"{nombre_base}_final_result.json")

    with open(final_json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "snapshot": snapshot,
                "result": resultado
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    final_report_file.write_text(final_report, encoding="utf-8")

    print("\n===== RESULTADO FINAL =====")
    print(f"Ticker: {ticker}")
    print(f"Precio inicial usado: {formatear_moneda(buy_price)}")
    print(f"Precio final usado: {formatear_moneda(sell_executed['close'])}")
    print(f"Valor final: {formatear_moneda(final_value)}")
    print(f"Ganancia/Pérdida: {formatear_moneda(profit)}")
    print(f"Retorno: {return_pct:.2f}%")
    print(f"Reporte final guardado en: {final_report_file}")
    print(f"Resultado JSON guardado en: {final_json_file}")
    print("===========================\n")

    ver_grafica = leer_texto("¿Desea ver la gráfica final? [s/n] ", "s").lower()
    if ver_grafica == "s":
        graficar_experimento(
            ticker=ticker,
            buy_dt=pd.Timestamp(snapshot["buy_executed"]["timestamp_real"]),
            eval_dt=pd.Timestamp(sell_executed["timestamp_real"]),
            buy_price=buy_price,
            sell_price=float(sell_executed["close"])
        )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=== EXPERIMENTO DE INVERSIÓN CON YAHOO FINANCE ===")
    print("1. Plan / registro inicial")
    print("2. Evaluación final")

    opcion = leer_texto("Seleccione una opción [1]: ", "1")

    try:
        if opcion == "1":
            modo_plan()
        elif opcion == "2":
            modo_evaluar()
        else:
            print("Opción no válida.")
            sys.exit(1)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()