"""
DVN Group 7 — CPI Australia Dashboard (Streamlit)
Built by Jacky Wang (Visual Designer)

Run with:
  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ====================================================================
# Page config — must be the first Streamlit command
# ====================================================================
st.set_page_config(
    page_title="CPI Australia — DVN Group 7",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====================================================================
# Design System — colour constants from DESIGN_SYSTEM.md
# ====================================================================
COLORS = {
    "primary": "#1B3A5C",
    "text": "#1A1A2E",
    "muted": "#6B7280",
    "grid": "#E5E7EB",
    "border": "#D1D5DB",
    "up": "#D64045",
    "down": "#1A8A6E",
    "warning": "#E8910C",
}

CPI_COLOR = "#D64045"  # Red = cost pressure
WPI_COLOR = "#3D6B99"  # Blue = wages

CITY_COLORS = {
    "Australia": "#1A1A2E",
    "Sydney": "#1B9E77",
    "Melbourne": "#D95F02",
    "Brisbane": "#7570B3",
    "Adelaide": "#E7298A",
    "Perth": "#66A61E",
    "Hobart": "#E6AB02",
    "Darwin": "#A6761D",
    "Canberra": "#666666",
}

EXP_COLORS = {
    "Food and non-alcoholic beverages": "#4E79A7",
    "Alcohol and tobacco": "#A0CBE8",
    "Clothing and footwear": "#F28E2B",
    "Housing": "#D64045",
    "Furnishings, household equipment and services": "#76B7B2",
    "Health": "#59A14F",
    "Transport": "#EDC948",
    "Communication": "#B07AA1",
    "Recreation and culture": "#FF9DA7",
    "Education": "#9C755F",
    "Insurance and financial services": "#BAB0AC",
}


# ====================================================================
# Data loading (cached so it only runs once)
# ====================================================================
@st.cache_data
def load_cpi_cities():
    """Load CPI Table 1 — city-level CPI index + YoY % change."""
    df = pd.read_excel("CPI_Table1.xlsx", sheet_name="Data1", header=None)
    cities = ["Australia", "Sydney", "Melbourne", "Brisbane",
              "Adelaide", "Perth", "Hobart", "Darwin", "Canberra"]

    data_rows = df.iloc[10:].copy()
    data_rows.columns = range(len(data_rows.columns))

    records = []
    for _, row in data_rows.iterrows():
        date = pd.to_datetime(row[0])
        for i, city in enumerate(cities):
            records.append({
                "date": date,
                "city": city,
                "cpi_index": pd.to_numeric(row[1 + i], errors="coerce"),
                "yoy_change": pd.to_numeric(row[10 + i], errors="coerce"),
            })
    return pd.DataFrame(records)


@st.cache_data
def load_wpi():
    """Load WPI Table 1 — national wage price index (quarterly)."""
    df = pd.read_excel("WPI_Table1.xlsx", sheet_name="Data1", header=None)
    data_rows = df.iloc[10:].copy()
    data_rows.columns = range(len(data_rows.columns))

    records = []
    for _, row in data_rows.iterrows():
        date = pd.to_datetime(row[0])
        records.append({
            "date": date,
            "wpi_index": pd.to_numeric(row[4], errors="coerce"),
            "wpi_yoy": pd.to_numeric(row[22], errors="coerce"),
        })
    result = pd.DataFrame(records)
    return result[result["date"] >= "2024-01-01"]


@st.cache_data
def load_expenditure():
    """Load CPI Table 9 — expenditure group CPI by city."""
    df = pd.read_excel("CPI_Table9.xlsx", sheet_name="Data1", header=None)

    cities_order = ["Sydney", "Melbourne", "Brisbane", "Adelaide",
                    "Perth", "Hobart", "Darwin", "Canberra"]
    exp_groups = [
        "All groups CPI",
        "Food and non-alcoholic beverages", "Alcohol and tobacco",
        "Clothing and footwear", "Housing",
        "Furnishings, household equipment and services",
        "Health", "Transport", "Communication",
        "Recreation and culture", "Education",
        "Insurance and financial services",
    ]

    data_rows = df.iloc[10:].copy()
    data_rows.columns = range(len(data_rows.columns))

    records = []
    for _, row in data_rows.iterrows():
        date = pd.to_datetime(row[0])
        col = 1
        for city in cities_order:
            for group in exp_groups:
                val = pd.to_numeric(row[col], errors="coerce") if col < len(row) else None
                records.append({
                    "date": date,
                    "city": city,
                    "group": group,
                    "cpi_index": val,
                })
                col += 1
    return pd.DataFrame(records)


# ====================================================================
# Chart theme — applies DVN Group 7 design system to Plotly figures
# ====================================================================
def apply_theme(fig, title=None):
    fig.update_layout(
        font=dict(family="Source Sans Pro, sans-serif", color=COLORS["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            gridcolor=COLORS["grid"],
            linecolor=COLORS["border"],
            tickfont=dict(size=12, color=COLORS["muted"]),
        ),
        yaxis=dict(
            gridcolor=COLORS["grid"],
            linecolor=COLORS["border"],
            tickfont=dict(size=12, color=COLORS["muted"]),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0, font=dict(size=12),
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    if title:
        fig.update_layout(
            title=dict(text=title, font=dict(size=16, color=COLORS["text"]),
                       x=0, xanchor="left")
        )
    return fig


# ====================================================================
# Load all data
# ====================================================================
cpi_cities = load_cpi_cities()
wpi = load_wpi()
expenditure = load_expenditure()


# ====================================================================
# Sidebar filters
# ====================================================================
st.sidebar.markdown("### 📊 Filters")

all_dates = cpi_cities["date"].sort_values().unique()
date_range = st.sidebar.select_slider(
    "Time range",
    options=pd.to_datetime(all_dates),
    value=(pd.to_datetime(all_dates[0]), pd.to_datetime(all_dates[-1])),
    format_func=lambda x: x.strftime("%b %Y"),
)

all_cities = ["Sydney", "Melbourne", "Brisbane", "Adelaide",
              "Perth", "Hobart", "Darwin", "Canberra"]
selected_cities = st.sidebar.multiselect(
    "Capital cities",
    options=all_cities,
    default=all_cities,
)

st.sidebar.markdown("---")
st.sidebar.caption("Source: ABS CPI (Cat. No. 6401.0); ABS WPI (Cat. No. 6345.0)")


# ====================================================================
# Filter data based on sidebar selections
# ====================================================================
mask = (
    (cpi_cities["date"] >= date_range[0]) &
    (cpi_cities["date"] <= date_range[1])
)
filtered_cpi = cpi_cities[mask]

mask_exp = (
    (expenditure["date"] >= date_range[0]) &
    (expenditure["date"] <= date_range[1]) &
    (expenditure["city"].isin(selected_cities))
)
filtered_exp = expenditure[mask_exp]


# ====================================================================
# Compact page CSS — single-page dashboard layout
# ====================================================================
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 100%; }
      h1.dash-title { font-size: 1.6rem; margin: 0 0 0.1rem 0; }
      .dash-sub { color: #6B7280; font-size: 0.85rem; margin-bottom: 0.6rem; }
      [data-testid="stMetric"] { background: #F7F9FC; padding: 8px 12px; border-radius: 8px; }
      [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
      [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
      .chart-title { font-size: 0.95rem; font-weight: 600; color: #1A1A2E; margin: 0.6rem 0 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ====================================================================
# Title + KPI metric cards
# ====================================================================
latest_aus = filtered_cpi[filtered_cpi["city"] == "Australia"].dropna(subset=["yoy_change"])
latest_cpi_val = latest_aus["yoy_change"].iloc[-1] if len(latest_aus) > 0 else None

latest_wpi_val = wpi["wpi_yoy"].dropna().iloc[-1] if len(wpi) > 0 else None

# Compute % change per expenditure group over the selected window (national avg across cities)
exp_change = pd.Series(dtype=float)
city_pressure = pd.Series(dtype=float)
top_group = "N/A"
top_group_pct = None
top_city = "N/A"
top_city_pct = None
top_city_group = "N/A"
top_group_city = "N/A"
top_group_city_pct = None

if len(filtered_exp) > 0 and filtered_exp["date"].nunique() > 1:
    first_date_g = filtered_exp["date"].min()
    last_date_g = filtered_exp["date"].max()

    # Per-(city, group) % change — same matrix the heatmap displays,
    # so CTA aggregates align with what the user sees in the cells.
    pivot_first_g = filtered_exp[filtered_exp["date"] == first_date_g] \
        .pivot_table(index="city", columns="group", values="cpi_index")
    pivot_last_g = filtered_exp[filtered_exp["date"] == last_date_g] \
        .pivot_table(index="city", columns="group", values="cpi_index")
    pct_matrix = ((pivot_last_g - pivot_first_g) / pivot_first_g * 100) \
        .drop(columns=["All groups CPI"], errors="ignore")

    exp_change = pct_matrix.mean(axis=0).dropna()
    if len(exp_change) > 0:
        top_group = exp_change.idxmax()
        top_group_pct = exp_change.max()

    # Hardest-hit city = the single brightest cell in the heatmap (city × category),
    # so the % shown in the CTA equals a value the user can read off the heatmap.
    city_pressure = pct_matrix.max(axis=1).dropna()
    if len(city_pressure) > 0:
        top_city = city_pressure.idxmax()
        top_city_pct = city_pressure.max()
        top_city_group = pct_matrix.loc[top_city].idxmax()

    # Within the top group, which city has the biggest jump? Single heatmap column.
    if top_group != "N/A" and top_group in pct_matrix.columns:
        gc_change = pct_matrix[top_group].dropna()
        if len(gc_change) > 0:
            top_group_city = gc_change.idxmax()
            top_group_city_pct = gc_change.max()

# Real wage gap (CPI minus WPI, latest)
real_gap = None
if latest_cpi_val is not None and latest_wpi_val is not None:
    real_gap = latest_cpi_val - latest_wpi_val

# Data-driven thesis line — replaces the static dash-sub so the headline
# reflects the current window/filter selection.
thesis_parts = []
if real_gap is not None:
    direction = "fallen" if real_gap > 0 else "risen"
    thesis_parts.append(
        f"Real wages have {direction} <b>{abs(real_gap):.1f} pp</b>"
    )
if top_city_group != "N/A" and top_city != "N/A" and top_city_pct is not None:
    thesis_parts.append(
        f"pain concentrates in <b>{top_city_group}</b>, "
        f"hitting <b>{top_city}</b> hardest (+{top_city_pct:.1f}%)"
    )
thesis = " · ".join(thesis_parts) if thesis_parts \
    else "Pressure differs by city, category, and household."

st.markdown(
    f'<h1 class="dash-title" style="color:{COLORS["primary"]};">CPI Australia · Cost-of-living dashboard</h1>'
    f'<div class="dash-sub">{thesis}</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Headline CPI (YoY)", f"{latest_cpi_val:.1f}%" if latest_cpi_val else "N/A")
col2.metric("WPI Growth (YoY)", f"{latest_wpi_val:.1f}%" if latest_wpi_val else "N/A")
col3.metric(
    "Real wage gap",
    f"{real_gap:+.1f} pp" if real_gap is not None else "N/A",
    help="CPI YoY minus WPI YoY. Positive = prices outpacing wages.",
)
col4.metric(
    "Fastest-rising category",
    top_group,
    f"{top_group_pct:+.1f}% over window" if top_group_pct is not None else None,
)

# ====================================================================
# Data-driven Key Insight — one concise line under the KPIs
# ====================================================================
if top_group != "N/A" and top_group_pct is not None:
    period_label = f"{filtered_exp['date'].min().strftime('%b %Y')}–{filtered_exp['date'].max().strftime('%b %Y')}"
    city_bit = (
        f" · sharpest in <b>{top_group_city}</b> (+{top_group_city_pct:.1f}%)"
        if top_group_city != "N/A" and top_group_city_pct is not None else ""
    )
    gap_bit = (
        f" · real-wage gap <b>{real_gap:+.1f} pp</b>"
        if real_gap is not None else ""
    )
    st.markdown(
        f"""
        <div style="background:#FFF8F0;border-left:3px solid {COLORS['up']};
                    padding:8px 14px;border-radius:6px;margin:8px 0 4px;font-size:0.88rem;">
            <b style="color:{COLORS['up']};">Insight</b> · {period_label} ·
            <b>{top_group}</b> leads at <b>{top_group_pct:+.1f}%</b>{city_bit}{gap_bit}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ====================================================================
# Chart grid — 2×2 single-page layout
# ====================================================================
CHART_HEIGHT = 290

# Prep data once for the row 1 charts
aus_cpi = filtered_cpi[filtered_cpi["city"] == "Australia"].copy()
aus_cpi["quarter"] = aus_cpi["date"].dt.to_period("Q")
cpi_quarterly = aus_cpi.groupby("quarter")["yoy_change"].mean().reset_index()
cpi_quarterly["date"] = cpi_quarterly["quarter"].dt.to_timestamp()
wpi_filtered = wpi[(wpi["date"] >= date_range[0]) & (wpi["date"] <= date_range[1])].copy()

city_data = filtered_cpi[
    (filtered_cpi["city"].isin(selected_cities)) &
    (filtered_cpi["yoy_change"].notna())
]

row1_left, row1_right = st.columns(2, gap="medium")

with row1_left:
    st.markdown('<div class="chart-title">Wages vs inflation (national)</div>', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=cpi_quarterly["date"], y=cpi_quarterly["yoy_change"],
        name="CPI", line=dict(color=CPI_COLOR, width=2.5), mode="lines+markers",
    ))
    fig1.add_trace(go.Scatter(
        x=wpi_filtered["date"], y=wpi_filtered["wpi_yoy"],
        name="WPI", line=dict(color=WPI_COLOR, width=2.5), mode="lines+markers",
    ))
    fig1.update_yaxes(title_text="YoY %")
    apply_theme(fig1)
    fig1.update_layout(height=CHART_HEIGHT, margin=dict(l=40, r=10, t=30, b=30))
    st.plotly_chart(fig1, use_container_width=True)

with row1_right:
    st.markdown('<div class="chart-title">CPI YoY by capital city</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    for city in selected_cities:
        city_df = city_data[city_data["city"] == city]
        fig2.add_trace(go.Scatter(
            x=city_df["date"], y=city_df["yoy_change"],
            name=city,
            line=dict(color=CITY_COLORS.get(city, "#999"), width=1.8),
            mode="lines",
        ))
    fig2.update_yaxes(title_text="YoY %")
    apply_theme(fig2)
    fig2.update_layout(height=CHART_HEIGHT, margin=dict(l=40, r=10, t=30, b=30))
    st.plotly_chart(fig2, use_container_width=True)

row2_left, row2_right = st.columns(2, gap="medium")

with row2_left:
    st.markdown('<div class="chart-title">Category change over period</div>', unsafe_allow_html=True)
    if len(filtered_exp) > 0 and filtered_exp["date"].nunique() > 1:
        first_date = filtered_exp["date"].min()
        last_date = filtered_exp["date"].max()
        first_vals = filtered_exp[filtered_exp["date"] == first_date].groupby("group")["cpi_index"].mean()
        last_vals = filtered_exp[filtered_exp["date"] == last_date].groupby("group")["cpi_index"].mean()
        pct_change = ((last_vals - first_vals) / first_vals * 100).dropna()
        pct_change = pct_change.drop("All groups CPI", errors="ignore").sort_values(ascending=True)
        top_in_chart = pct_change.idxmax()
        colors = [COLORS["up"] if g == top_in_chart else EXP_COLORS.get(g, "#999") for g in pct_change.index]
        opacities = [1.0 if g == top_in_chart else 0.5 for g in pct_change.index]
        fig3 = go.Figure(go.Bar(
            x=pct_change.values, y=pct_change.index, orientation="h",
            marker=dict(color=colors, opacity=opacities),
            text=[f"{v:.1f}%" for v in pct_change.values],
            textposition="outside",
            textfont=dict(size=10),
        ))
        fig3.update_xaxes(title_text="% change")
        apply_theme(fig3)
        fig3.update_layout(height=CHART_HEIGHT, margin=dict(l=10, r=40, t=20, b=30),
                           yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Not enough data.")

with row2_right:
    st.markdown('<div class="chart-title">City × category heatmap</div>', unsafe_allow_html=True)
    if len(filtered_exp) > 0 and filtered_exp["date"].nunique() > 1:
        first_date = filtered_exp["date"].min()
        last_date = filtered_exp["date"].max()
        exp_first = filtered_exp[filtered_exp["date"] == first_date].copy()
        exp_last = filtered_exp[filtered_exp["date"] == last_date].copy()
        pivot_first = exp_first.pivot_table(index="city", columns="group", values="cpi_index")
        pivot_last = exp_last.pivot_table(index="city", columns="group", values="cpi_index")
        hm_data = ((pivot_last - pivot_first) / pivot_first * 100)
        hm_data = hm_data.drop(columns=["All groups CPI"], errors="ignore").dropna(axis=1, how="all")
        hm_data = hm_data.loc[
            hm_data.mean(axis=1).sort_values(ascending=True).index,
            hm_data.mean(axis=0).sort_values(ascending=False).index,
        ]
        fig4 = go.Figure(go.Heatmap(
            z=hm_data.values, x=hm_data.columns, y=hm_data.index,
            colorscale=[[0.0, "#1A8A6E"], [0.5, "#FAFBFC"], [1.0, "#D64045"]],
            text=hm_data.round(1).values, texttemplate="%{text}", textfont=dict(size=9),
            hovertemplate="%{y} · %{x}: %{z:.1f}%<extra></extra>",
            colorbar=dict(title="%", thickness=10, len=0.8),
        ))
        apply_theme(fig4)
        fig4.update_layout(
            height=CHART_HEIGHT,
            margin=dict(l=10, r=10, t=20, b=60),
            xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Not enough data.")


# ====================================================================
# Recommended next steps — terse, data-driven
# ====================================================================
if top_group != "N/A" and top_group_pct is not None and len(exp_change) > 0:
    sorted_groups = exp_change.sort_values(ascending=False)
    runner_up = sorted_groups.index[1] if len(sorted_groups) > 1 else None
    runner_up_pct = sorted_groups.iloc[1] if len(sorted_groups) > 1 else None

    bullets = [
        f"Investigate <b style='color:{COLORS['up']};'>{top_group}</b> drivers ({top_group_pct:+.1f}%)"
        + (f" — start with <b>{top_group_city}</b>" if top_group_city != "N/A" else "")
    ]
    if runner_up is not None:
        bullets.append(f"Watch next-fastest: <b>{runner_up}</b> ({runner_up_pct:+.1f}%)")
    if real_gap is not None and real_gap > 0:
        bullets.append(f"Close real-wage gap ({real_gap:+.1f} pp)")
    if top_city != "N/A":
        cat_bit = f" on <b>{top_city_group}</b>" if top_city_group != "N/A" else ""
        bullets.append(f"Target hardest-hit city: <b>{top_city}</b>{cat_bit} (+{top_city_pct:.1f}%)")

    items_html = "".join(
        f'<div style="flex:1;min-width:200px;padding:10px 14px;background:#fff;'
        f'border-left:4px solid {COLORS["primary"]};border-radius:4px;'
        f'font-size:1.0rem;line-height:1.35;display:flex;gap:10px;align-items:flex-start;">'
        f'<span style="font-size:1.25rem;font-weight:800;color:{COLORS["primary"]};'
        f'line-height:1;flex-shrink:0;">{i}</span>'
        f'<span>{b}</span></div>'
        for i, b in enumerate(bullets, start=1)
    )
    st.markdown(
        f"""
        <div style="background:#F7F9FC;padding:14px 16px;border-radius:8px;margin-top:10px;">
            <div style="font-size:0.85rem;font-weight:700;color:{COLORS['primary']};
                        letter-spacing:0.6px;text-transform:uppercase;margin-bottom:10px;">
                Next steps
            </div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">{items_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f'<div style="font-size:0.7rem;color:{COLORS["muted"]};margin-top:6px;text-align:right;">'
    f'ABS CPI 6401.0 · ABS WPI 6345.0</div>',
    unsafe_allow_html=True,
)
