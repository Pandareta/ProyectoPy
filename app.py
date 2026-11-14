"""Dashboard ejecutivo de e-commerce (capa de presentación).

Consume `data/raw/ecommerce_orders.csv`, aplica el pipeline de limpieza
definido en la skill `data-cleaning-etl` y expone KPIs y gráficos
interactivos para un perfil de Data Analyst / Business Intelligence.

Uso:
    streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / "data" / "raw" / "ecommerce_orders.csv"
SQL_PATH = BASE_DIR / "sql" / "analytics_queries.sql"

DELAY_THRESHOLD_DAYS = 6

PRIMARY_COLOR = "#2DD4BF"
CHART_COLORS = ["#2DD4BF", "#60A5FA", "#A78BFA", "#F472B6", "#FBBF24", "#34D399"]

st.set_page_config(
    page_title="E-commerce Analytics | Portfolio BI",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------
# Formato local (español): miles con punto y decimales con coma.
# ---------------------------------------------------------------------
def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value: float, decimals: int = 0) -> str:
    formatted = f"{value:,.{decimals}f}"
    return "$" + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_pct(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f} %".replace(".", ",")


def pct_delta(current: float, previous: float) -> float | None:
    if previous == 0 or pd.isna(previous):
        return None
    return (current / previous - 1) * 100


def format_delta(value: float, suffix: str) -> str:
    number = f"{value:+.1f}".replace(".", ",")
    return f"{number} {suffix} vs. mes anterior"


# ---------------------------------------------------------------------
# Carga y limpieza (cacheada para no repetir el trabajo en cada render).
# ---------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando y limpiando el dataset...")
def load_and_clean(csv_path: str) -> tuple[pd.DataFrame, dict[str, int]]:
    raw = pd.read_csv(csv_path, parse_dates=["order_date"])
    raw_rows = len(raw)

    # 1. Deduplicación explícita y contabilizada.
    duplicates_removed = int(raw.duplicated().sum())
    df = raw.drop_duplicates().copy()

    # 2. Imputación de precio con la mediana por categoría (robusta a outliers).
    price_nulls = int(df["price"].isna().sum())
    df["price"] = df["price"].fillna(
        df.groupby("category")["price"].transform("median")
    )

    # 3. Categóricas nulas: se conservan las filas y se marca el nulo.
    region_nulls = int(df["region"].isna().sum())
    df["region"] = df["region"].fillna("No Especificada")
    df["category"] = df["category"].fillna("No Especificada")

    # 4. Feature engineering vectorizado.
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["is_delayed"] = df["shipping_days"] > DELAY_THRESHOLD_DAYS
    df["shipping_bucket"] = pd.cut(
        df["shipping_days"],
        bins=[0, 3, 6, 9, float("inf")],
        labels=["1-3 días", "4-6 días", "7-9 días", "10+ días"],
        right=True,
    )

    stats = {
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "duplicates_removed": duplicates_removed,
        "price_imputed": price_nulls,
        "region_imputed": region_nulls,
    }
    return df, stats


def month_over_month(
    df: pd.DataFrame, column: str, aggregation: str
) -> tuple[float, float] | tuple[None, None]:
    series = df.groupby("month")[column].agg(aggregation).sort_index()
    if len(series) < 2:
        return None, None
    return float(series.iloc[-1]), float(series.iloc[-2])


def style_figure(fig, height: int = 360):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=10, t=48, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=12),
    )
    return fig


# ---------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------
if not RAW_PATH.exists():
    st.error(
        "No se encontró `data/raw/ecommerce_orders.csv`. "
        "Ejecuta `python src/generate_data.py` para generarlo."
    )
    st.stop()

df, stats = load_and_clean(str(RAW_PATH))

# ---------------------------------------------------------------------
# Filtros laterales
# ---------------------------------------------------------------------
st.sidebar.header("Filtros")

region_options = sorted(df["region"].unique())
category_options = sorted(df["category"].unique())
payment_options = sorted(df["payment_method"].unique())

selected_regions = st.sidebar.multiselect(
    "Región", region_options, default=region_options
)
selected_categories = st.sidebar.multiselect(
    "Categoría", category_options, default=category_options
)
selected_payments = st.sidebar.multiselect(
    "Método de pago", payment_options, default=payment_options
)

st.sidebar.caption("Sin selección = se muestran todos los valores.")

# Un multiselect vacío se interpreta como "sin filtro".
regions = selected_regions or region_options
categories = selected_categories or category_options
payments = selected_payments or payment_options

filtered = df[
    df["region"].isin(regions)
    & df["category"].isin(categories)
    & df["payment_method"].isin(payments)
].copy()

# ---------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------
st.title("E-commerce Analytics")
st.caption(
    "Portfolio de Data Analyst & Business Intelligence · "
    f"{format_number(stats['clean_rows'])} órdenes · "
    f"{df['order_date'].min():%d/%m/%Y} a {df['order_date'].max():%d/%m/%Y}"
)

clean_pct = stats["clean_rows"] / stats["raw_rows"] * 100
st.subheader("Calidad de datos")
st.markdown(
    f"**{format_number(stats['clean_rows'])} filas limpias de "
    f"{format_number(stats['raw_rows'])} crudas ({format_pct(clean_pct)}).** "
    f"Se eliminaron {stats['duplicates_removed']} duplicados, se imputaron "
    f"{stats['price_imputed']} precios con la mediana por categoría y "
    f"{stats['region_imputed']} regiones como *No Especificada*."
)

if filtered.empty:
    st.warning("Los filtros seleccionados no devuelven órdenes. Amplía la selección.")
    st.stop()

# ---------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------
revenue = float(filtered["price"].sum())
orders_count = int(len(filtered))
average_order_value = float(filtered["price"].mean())
positive_reviews = float((filtered["review_score"] >= 4).mean() * 100)

rev_now, rev_prev = month_over_month(filtered, "price", "sum")
ord_now, ord_prev = month_over_month(filtered, "price", "count")
aov_now, aov_prev = month_over_month(filtered, "price", "mean")
pos_now, pos_prev = None, None
monthly_positive = (
    filtered.assign(is_positive=filtered["review_score"] >= 4)
    .groupby("month")["is_positive"]
    .mean()
    .sort_index()
)
if len(monthly_positive) >= 2:
    pos_now = float(monthly_positive.iloc[-1] * 100)
    pos_prev = float(monthly_positive.iloc[-2] * 100)

revenue_delta = pct_delta(rev_now, rev_prev) if rev_now is not None else None
orders_delta = pct_delta(ord_now, ord_prev) if ord_now is not None else None
aov_delta = pct_delta(aov_now, aov_prev) if aov_now is not None else None
positive_delta = (
    pos_now - pos_prev if pos_now is not None and pos_prev is not None else None
)

kpi_columns = st.columns(4)
kpi_columns[0].metric(
    "Ingresos totales",
    format_currency(revenue),
    delta=None if revenue_delta is None else format_delta(revenue_delta, "%"),
)
kpi_columns[1].metric(
    "Órdenes",
    format_number(orders_count),
    delta=None if orders_delta is None else format_delta(orders_delta, "%"),
)
kpi_columns[2].metric(
    "Ticket promedio",
    format_currency(average_order_value, 2),
    delta=None if aov_delta is None else format_delta(aov_delta, "%"),
)
kpi_columns[3].metric(
    "Reseñas positivas (4-5 ★)",
    format_pct(positive_reviews),
    delta=None if positive_delta is None else format_delta(positive_delta, "pp"),
)

st.caption(
    "Los deltas comparan el último mes disponible con el mes anterior dentro "
    "del periodo filtrado."
)

# ---------------------------------------------------------------------
# Gráficos (grilla 2x2)
# ---------------------------------------------------------------------
monthly_revenue = (
    filtered.groupby("month", as_index=False)["price"].sum().sort_values("month")
)

fig_revenue = px.area(
    monthly_revenue,
    x="month",
    y="price",
    color_discrete_sequence=[PRIMARY_COLOR],
    labels={"month": "Mes", "price": "Ingresos (USD)"},
)
fig_revenue.update_traces(
    line=dict(width=3),
    fillcolor="rgba(45, 212, 191, 0.18)",
    hovertemplate="%{x|%b %Y}<br>Ingresos: $%{y:,.0f}<extra></extra>",
)
fig_revenue.update_layout(
    title="Evolución mensual de ingresos",
    xaxis_title=None,
    yaxis_title="Ingresos (USD)",
    yaxis_tickprefix="$",
    yaxis_tickformat=",.0f",
    showlegend=False,
)
style_figure(fig_revenue)

shipping_impact = (
    filtered.groupby("shipping_bucket", observed=True)
    .agg(avg_review=("review_score", "mean"), orders=("order_id", "count"))
    .reset_index()
)
fig_shipping = px.bar(
    shipping_impact,
    x="shipping_bucket",
    y="avg_review",
    color="avg_review",
    color_continuous_scale="RdYlGn",
    range_color=[1, 5],
    text_auto=".2f",
    labels={
        "shipping_bucket": "Días de envío",
        "avg_review": "Reseña promedio",
    },
)
fig_shipping.update_traces(
    textposition="outside",
    customdata=shipping_impact[["orders"]],
    hovertemplate=(
        "Envío: %{x}<br>Reseña promedio: %{y:.2f} / 5"
        "<br>Órdenes: %{customdata[0]:,}<extra></extra>"
    ),
)
fig_shipping.update_layout(
    title="Impacto de los días de envío en la reseña",
    xaxis_title=None,
    yaxis_title="Reseña promedio (1-5)",
    yaxis_range=[0, 5.5],
    coloraxis_showscale=False,
)
style_figure(fig_shipping)

category_revenue = (
    filtered.groupby("category", as_index=False)["price"]
    .sum()
    .sort_values("price")
)
category_revenue["label"] = category_revenue["price"].map(format_currency)
fig_category = px.bar(
    category_revenue,
    x="price",
    y="category",
    orientation="h",
    text="label",
    color="price",
    color_continuous_scale="Teal",
    labels={"price": "Ingresos (USD)", "category": "Categoría"},
)
fig_category.update_traces(textposition="outside")
fig_category.update_layout(
    title="Facturación por categoría",
    xaxis_title="Ingresos (USD)",
    yaxis_title=None,
    xaxis_tickprefix="$",
    xaxis_tickformat=",.0f",
    coloraxis_showscale=False,
)
style_figure(fig_category)

payment_mix = (
    filtered["payment_method"]
    .value_counts()
    .rename_axis("payment_method")
    .reset_index(name="orders")
)
fig_payment = px.pie(
    payment_mix,
    names="payment_method",
    values="orders",
    hole=0.45,
    color_discrete_sequence=CHART_COLORS,
)
fig_payment.update_traces(
    textinfo="percent",
    textposition="inside",
    hovertemplate="%{label}<br>%{value:,} órdenes (%{percent})<extra></extra>",
)
fig_payment.update_layout(
    title="Distribución de métodos de pago",
    legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0),
)
style_figure(fig_payment)

left, right = st.columns(2)
left.plotly_chart(fig_revenue, width="stretch")
right.plotly_chart(fig_shipping, width="stretch")

left, right = st.columns(2)
left.plotly_chart(fig_category, width="stretch")
right.plotly_chart(fig_payment, width="stretch")

# ---------------------------------------------------------------------
# Consultas SQL para revisores
# ---------------------------------------------------------------------
with st.expander("Ver las consultas SQL del análisis"):
    st.caption(
        "Código fuente en `sql/analytics_queries.sql`: participación de ingresos, "
        "top clientes por región, impacto logístico y recurrencia con `LAG()`."
    )
    if SQL_PATH.exists():
        st.code(SQL_PATH.read_text(encoding="utf-8"), language="sql")
    else:
        st.warning("No se encontró `sql/analytics_queries.sql`.")

st.markdown("---")
st.caption(
    "Dataset sintético reproducible (seed 42) con fines de portafolio. "
    "Precios en USD; la limpieza se ejecuta en cada carga y está cacheada."
)
