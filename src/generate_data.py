"""Genera el dataset reproducible de órdenes de e-commerce.

El script crea 15.000 órdenes entre 2025-01-01 y 2026-10-31 con una semilla
fija (42) e inyecta suciedad controlada para que la capa de limpieza tenga
casos reales que resolver: nulos en `price`, nulos en `region` y duplicados.

Uso:
    python src/generate_data.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ORDERS = 15_000
N_CUSTOMERS = 12_000
START_DATE = pd.Timestamp("2025-01-01")
END_DATE = pd.Timestamp("2026-10-31")

NULL_PRICES = 120
NULL_REGIONS = 80
DUPLICATED_ROWS = 50

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = BASE_DIR / "data" / "raw" / "ecommerce_orders.csv"

CATEGORIES = [
    "Electrónica",
    "Ropa y Accesorios",
    "Hogar y Cocina",
    "Belleza",
    "Deportes",
    "Libros",
]
CATEGORY_WEIGHTS = [0.22, 0.24, 0.18, 0.12, 0.12, 0.12]

REGIONS = ["Norte", "Centro", "Sur", "Este", "Oeste"]
REGION_WEIGHTS = [0.24, 0.28, 0.20, 0.16, 0.12]

PAYMENT_METHODS = ["Tarjeta de crédito", "PayPal", "Transferencia", "Efectivo"]
PAYMENT_WEIGHTS = [0.45, 0.25, 0.18, 0.12]

# Poisson(4) + 1: media de 5 días de envío, con ~21 % de pedidos sobre 6 días.
SHIPPING_LAMBDA = 4.0
DELAY_THRESHOLD_DAYS = 6

LOGGER = logging.getLogger("generate_data")


def build_clean_orders(rng: np.random.Generator) -> pd.DataFrame:
    """Construye las 15.000 órdenes base sin suciedad inyectada."""
    order_ids = [f"ORD-{i:06d}" for i in range(1, N_ORDERS + 1)]
    customer_ids = [
        f"CUST-{i:05d}" for i in rng.integers(1, N_CUSTOMERS + 1, size=N_ORDERS)
    ]

    span_days = (END_DATE - START_DATE).days
    order_dates = START_DATE + pd.to_timedelta(
        rng.integers(0, span_days + 1, size=N_ORDERS), unit="D"
    )

    categories = rng.choice(CATEGORIES, size=N_ORDERS, p=CATEGORY_WEIGHTS)
    regions = rng.choice(REGIONS, size=N_ORDERS, p=REGION_WEIGHTS)
    payment_methods = rng.choice(
        PAYMENT_METHODS, size=N_ORDERS, p=PAYMENT_WEIGHTS
    )

    # Log-normal con mediana ~95 y cola derecha de pedidos de alto valor.
    prices = np.round(rng.lognormal(mean=np.log(95.0), sigma=0.55, size=N_ORDERS), 2)

    shipping_days = rng.poisson(SHIPPING_LAMBDA, size=N_ORDERS) + 1

    review_scores = rng.choice(
        [1, 2, 3, 4, 5], size=N_ORDERS, p=[0.05, 0.07, 0.13, 0.35, 0.40]
    )
    is_delayed = shipping_days > DELAY_THRESHOLD_DAYS
    review_scores[is_delayed] = rng.choice(
        [1, 2, 3], size=int(is_delayed.sum()), p=[0.55, 0.30, 0.15]
    )

    return pd.DataFrame(
        {
            "order_id": order_ids,
            "customer_id": customer_ids,
            "order_date": order_dates,
            "category": categories,
            "region": regions,
            "payment_method": payment_methods,
            "price": prices,
            "shipping_days": shipping_days,
            "review_score": review_scores,
        }
    )


def inject_dirt(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Añade nulos y duplicados respetando los conteos exactos esperados."""
    dirty = df.copy()

    null_price_idx = rng.choice(dirty.index, size=NULL_PRICES, replace=False)
    dirty.loc[null_price_idx, "price"] = np.nan

    null_region_idx = rng.choice(dirty.index, size=NULL_REGIONS, replace=False)
    dirty.loc[null_region_idx, "region"] = np.nan

    # Los duplicados salen de filas completas para no alterar los conteos de nulos.
    complete_rows = dirty.index[dirty["price"].notna() & dirty["region"].notna()]
    duplicated_idx = rng.choice(complete_rows, size=DUPLICATED_ROWS, replace=False)
    dirty = pd.concat([dirty, dirty.loc[duplicated_idx]], ignore_index=True)

    return dirty.sample(frac=1.0, random_state=SEED + 2).reset_index(drop=True)


def validate(df: pd.DataFrame) -> None:
    """Comprueba que el dataset generado cumple el contrato esperado."""
    assert len(df) == N_ORDERS + DUPLICATED_ROWS, "Número de filas inesperado"
    assert int(df["price"].isna().sum()) == NULL_PRICES, "Nulos en price inesperados"
    assert int(df["region"].isna().sum()) == NULL_REGIONS, "Nulos en region inesperados"
    assert int(df.duplicated().sum()) == DUPLICATED_ROWS, "Duplicados inesperados"
    assert df["order_date"].between(START_DATE, END_DATE).all(), "Fechas fuera de rango"
    assert df["review_score"].between(1, 5).all(), "review_score fuera de 1-5"
    assert df["shipping_days"].min() >= 1, "shipping_days debe ser >= 1"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    rng = np.random.default_rng(SEED)
    orders = build_clean_orders(rng)
    dataset = inject_dirt(orders, rng)
    validate(dataset)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False, date_format="%Y-%m-%d", encoding="utf-8")

    delayed_share = (dataset["shipping_days"] > DELAY_THRESHOLD_DAYS).mean() * 100
    LOGGER.info("Dataset escrito en %s", OUTPUT_PATH)
    LOGGER.info(
        "Filas: %d | nulos price: %d | nulos region: %d | duplicados: %d",
        len(dataset),
        int(dataset["price"].isna().sum()),
        int(dataset["region"].isna().sum()),
        int(dataset.duplicated().sum()),
    )
    LOGGER.info("Pedidos con envío > %d días: %.1f %%", DELAY_THRESHOLD_DAYS, delayed_share)


if __name__ == "__main__":
    main()
