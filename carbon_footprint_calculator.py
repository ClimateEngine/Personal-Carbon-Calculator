"""
carbon_footprint_calculator.py
--------------------------------
Personal Carbon Footprint Calculator — SINGLE-FILE VERSION

This file merges the full modular project (app.py, calculator.py,
emission_factors.py, benchmark.py, recommendations.py, charts.py) into one
script so it can be run directly in PyCharm (or any IDE) with zero import
setup.

HOW TO RUN IN PYCHARM:
1. Open this file in PyCharm.
2. Open the Terminal tab at the bottom of PyCharm.
3. Install dependencies:
       pip install streamlit plotly
4. Run the app (Streamlit apps must be launched via the CLI, not the ▶ Run
   button, since they start a local web server):
       streamlit run carbon_footprint_calculator.py
5. It will open automatically in your browser at http://localhost:8501

NOTE: For a real GitHub/portfolio submission, prefer the modular multi-file
version (app.py, calculator.py, emission_factors.py, benchmark.py,
recommendations.py, charts.py) — it's better structured for readability,
testing, and maintainability. This single-file version exists purely for
quick local verification.

Author: Atharva | Climate Tech / ESG Portfolio Project
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# SECTION 1: EMISSION FACTORS  (formerly emission_factors.py)
# =============================================================================
#
# IMPORTANT — DATA DISCLAIMER
# All values below are illustrative, India-focused approximations compiled
# for demonstration purposes. Before using this tool for any real reporting,
# academic, or advisory work, replace these with verified figures from
# authoritative sources such as:
#   - India GHG Program / MoEFCC National Communications
#   - IPCC Emission Factor Database (EFDB)
#   - DEFRA / BEIS Greenhouse Gas Conversion Factors
#   - IEA Emission Factors for Electricity
#   - GLEC Framework (for freight/logistics-related transport)

# --- Electricity (kg CO2 per kWh) -------------------------------------------
ELECTRICITY_EMISSION_FACTOR: Dict[str, float] = {
    "India": 0.82,  # kgCO2/kWh — update from latest CEA CO2 Baseline Database
}

# --- Transportation (kg CO2 per passenger-km) -------------------------------
TRANSPORT_EMISSION_FACTORS: Dict[str, float] = {
    "Petrol Car": 0.192,
    "Diesel Car": 0.171,
    "Hybrid Car": 0.106,
    "Electric Vehicle": 0.053,  # grid-dependent; assumes India grid mix
    "Motorcycle": 0.083,
    "Bus": 0.082,
    "Metro": 0.041,
    "Train": 0.041,
    "Bicycle": 0.0,
    "Walking": 0.0,
}

TRANSPORT_ICONS: Dict[str, str] = {
    "Petrol Car": "🚗",
    "Diesel Car": "🚙",
    "Hybrid Car": "🔋🚗",
    "Electric Vehicle": "⚡🚗",
    "Motorcycle": "🏍️",
    "Bus": "🚌",
    "Metro": "🚇",
    "Train": "🚆",
    "Bicycle": "🚲",
    "Walking": "🚶",
}

# --- Diet (kg CO2e per meal) -------------------------------------------------
DIET_EMISSION_FACTORS: Dict[str, float] = {
    "Vegan": 0.50,
    "Vegetarian": 0.70,
    "Eggetarian": 0.90,
    "Chicken-based Diet": 1.40,
    "Mixed Diet": 1.90,
    "High Meat Diet": 2.50,
}

DIET_ICONS: Dict[str, str] = {
    "Vegan": "🌱",
    "Vegetarian": "🥦",
    "Eggetarian": "🥚",
    "Chicken-based Diet": "🍗",
    "Mixed Diet": "🍽️",
    "High Meat Diet": "🥩",
}

# --- Air travel (kg CO2 per flight, per passenger) ---------------------------
FLIGHT_EMISSION_FACTORS: Dict[str, float] = {
    "Domestic Flight": 250.0,
    "International Flight": 1100.0,
}

# --- Waste (kg CO2e per kg of waste) -----------------------------------------
WASTE_EMISSION_FACTORS: Dict[str, float] = {
    "Landfill": 0.58,
    "Recycling": 0.10,
    "Composting": 0.05,
}

WASTE_ICONS: Dict[str, str] = {
    "Landfill": "🗑️",
    "Recycling": "♻️",
    "Composting": "🌿",
}

# --- National / global benchmarks (tonnes CO2 per person per year) ---------
BENCHMARKS: Dict[str, float] = {
    "India": 1.9,
    "World Average": 4.7,
    "France": 4.0,
    "Germany": 7.5,
    "USA": 14.0,
}


@dataclass(frozen=True)
class UnitAssumptions:
    """Conversion constants used to annualize user-entered periodic values."""

    DAYS_PER_YEAR: int = 365
    WEEKS_PER_YEAR: int = 52
    MONTHS_PER_YEAR: int = 12
    KG_PER_TONNE: int = 1000


UNITS = UnitAssumptions()


# =============================================================================
# SECTION 2: CALCULATOR  (formerly calculator.py)
# =============================================================================

@dataclass
class UserInputs:
    """Raw, validated inputs collected from the Streamlit UI."""

    country: str
    transport_mode: str
    daily_distance_km: float
    monthly_electricity_kwh: float
    diet_type: str
    meals_per_day: float
    domestic_flights: int
    international_flights: int
    weekly_waste_kg: float
    waste_disposal_method: str


@dataclass
class EmissionResults:
    """Annual emissions (in tonnes CO2e) broken down by category."""

    transportation: float = 0.0
    electricity: float = 0.0
    diet: float = 0.0
    air_travel: float = 0.0
    waste: float = 0.0
    total: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.total = round(
            self.transportation
            + self.electricity
            + self.diet
            + self.air_travel
            + self.waste,
            2,
        )

    def as_dict(self) -> Dict[str, float]:
        return {
            "Transportation": self.transportation,
            "Electricity": self.electricity,
            "Diet": self.diet,
            "Air Travel": self.air_travel,
            "Waste": self.waste,
        }


def clamp_non_negative(value: float) -> float:
    """Guards against negative inputs, which are physically meaningless
    for distances, consumption, or counts in this calculator."""
    if value is None:
        return 0.0
    return max(0.0, float(value))


def calculate_transportation_emissions(mode: str, daily_distance_km: float) -> float:
    daily_distance_km = clamp_non_negative(daily_distance_km)
    factor = TRANSPORT_EMISSION_FACTORS.get(mode, 0.0)
    annual_km = daily_distance_km * UNITS.DAYS_PER_YEAR
    annual_kg = factor * annual_km
    return annual_kg / UNITS.KG_PER_TONNE


def calculate_electricity_emissions(country: str, monthly_kwh: float) -> float:
    monthly_kwh = clamp_non_negative(monthly_kwh)
    factor = ELECTRICITY_EMISSION_FACTOR.get(country, 0.0)
    annual_kwh = monthly_kwh * UNITS.MONTHS_PER_YEAR
    annual_kg = factor * annual_kwh
    return annual_kg / UNITS.KG_PER_TONNE


def calculate_diet_emissions(diet_type: str, meals_per_day: float) -> float:
    meals_per_day = clamp_non_negative(meals_per_day)
    factor = DIET_EMISSION_FACTORS.get(diet_type, 0.0)
    annual_meals = meals_per_day * UNITS.DAYS_PER_YEAR
    annual_kg = factor * annual_meals
    return annual_kg / UNITS.KG_PER_TONNE


def calculate_air_travel_emissions(domestic_flights: int, international_flights: int) -> float:
    domestic_flights = clamp_non_negative(domestic_flights)
    international_flights = clamp_non_negative(international_flights)
    annual_kg = (
        domestic_flights * FLIGHT_EMISSION_FACTORS["Domestic Flight"]
        + international_flights * FLIGHT_EMISSION_FACTORS["International Flight"]
    )
    return annual_kg / UNITS.KG_PER_TONNE


def calculate_waste_emissions(weekly_waste_kg: float, disposal_method: str) -> float:
    weekly_waste_kg = clamp_non_negative(weekly_waste_kg)
    factor = WASTE_EMISSION_FACTORS.get(disposal_method, 0.0)
    annual_kg_waste = weekly_waste_kg * UNITS.WEEKS_PER_YEAR
    annual_kg_co2 = factor * annual_kg_waste
    return annual_kg_co2 / UNITS.KG_PER_TONNE


def calculate_all_emissions(inputs: UserInputs) -> EmissionResults:
    transportation = round(
        calculate_transportation_emissions(inputs.transport_mode, inputs.daily_distance_km), 2
    )
    electricity = round(
        calculate_electricity_emissions(inputs.country, inputs.monthly_electricity_kwh), 2
    )
    diet = round(calculate_diet_emissions(inputs.diet_type, inputs.meals_per_day), 2)
    air_travel = round(
        calculate_air_travel_emissions(inputs.domestic_flights, inputs.international_flights), 2
    )
    waste = round(
        calculate_waste_emissions(inputs.weekly_waste_kg, inputs.waste_disposal_method), 2
    )

    return EmissionResults(
        transportation=transportation,
        electricity=electricity,
        diet=diet,
        air_travel=air_travel,
        waste=waste,
    )


# =============================================================================
# SECTION 3: BENCHMARK COMPARISON  (formerly benchmark.py)
# =============================================================================

NEAR_AVERAGE_TOLERANCE = 0.15  # +/- 15%


@dataclass
class BenchmarkResult:
    reference_label: str
    reference_value: float
    status: str  # "Below Average" | "Near Average" | "Above Average"
    explanation: str


def compare_to_benchmark(total_emissions: float, reference: str = "India") -> BenchmarkResult:
    reference_value = BENCHMARKS.get(reference, BENCHMARKS["World Average"])
    lower_bound = reference_value * (1 - NEAR_AVERAGE_TOLERANCE)
    upper_bound = reference_value * (1 + NEAR_AVERAGE_TOLERANCE)

    if total_emissions < lower_bound:
        status = "Below Average"
        explanation = (
            f"Your footprint is meaningfully lower than the {reference} average of "
            f"{reference_value} t CO₂/year — great work, keep it up!"
        )
    elif total_emissions > upper_bound:
        status = "Above Average"
        explanation = (
            f"Your footprint is meaningfully higher than the {reference} average of "
            f"{reference_value} t CO₂/year. Check the recommendations below to bring it down."
        )
    else:
        status = "Near Average"
        explanation = (
            f"Your footprint is close to the {reference} average of "
            f"{reference_value} t CO₂/year — there's still room to improve."
        )

    return BenchmarkResult(
        reference_label=reference,
        reference_value=reference_value,
        status=status,
        explanation=explanation,
    )


def get_all_benchmarks_table(total_emissions: float) -> List[Tuple[str, float, float]]:
    rows = []
    for label, value in BENCHMARKS.items():
        rows.append((label, value, round(total_emissions - value, 2)))
    return rows


# =============================================================================
# SECTION 4: RECOMMENDATIONS ENGINE  (formerly recommendations.py)
# =============================================================================

@dataclass
class Recommendation:
    icon: str
    text: str
    potential_reduction_tonnes: float  # estimated annual tonnes CO2 saved


HIGH_EMISSION_TRANSPORT_MODES = {"Petrol Car", "Diesel Car"}
LOWER_EMISSION_ALTERNATIVE = "Bus"  # conservative substitution benchmark


def generate_recommendations(
    inputs: UserInputs, results: EmissionResults
) -> List[Recommendation]:
    recommendations: List[Recommendation] = []

    # --- Transportation -----------------------------------------------
    if inputs.transport_mode in HIGH_EMISSION_TRANSPORT_MODES and inputs.daily_distance_km > 0:
        current_factor = TRANSPORT_EMISSION_FACTORS[inputs.transport_mode]
        alt_factor = TRANSPORT_EMISSION_FACTORS[LOWER_EMISSION_ALTERNATIVE]
        annual_km = inputs.daily_distance_km * UNITS.DAYS_PER_YEAR
        saving_kg = (current_factor - alt_factor) * annual_km
        saving_tonnes = round(max(saving_kg, 0) / UNITS.KG_PER_TONNE, 2)
        if saving_tonnes > 0:
            recommendations.append(
                Recommendation(
                    icon="🚌",
                    text=(
                        f"Switch some {inputs.transport_mode.lower()} trips to public transport "
                        "or carpooling to cut commute emissions."
                    ),
                    potential_reduction_tonnes=saving_tonnes,
                )
            )

    if inputs.transport_mode != "Electric Vehicle" and results.transportation > 1.0:
        recommendations.append(
            Recommendation(
                icon="⚡",
                text="Consider switching to an Electric Vehicle for your commute over time.",
                potential_reduction_tonnes=round(results.transportation * 0.4, 2),
            )
        )

    # --- Electricity -----------------------------------------------------
    if results.electricity > 0.5:
        recommendations.append(
            Recommendation(
                icon="💡",
                text="Switch to LED bulbs and energy-efficient appliances to reduce electricity use.",
                potential_reduction_tonnes=round(results.electricity * 0.15, 2),
            )
        )
    if inputs.monthly_electricity_kwh > 200:
        recommendations.append(
            Recommendation(
                icon="☀️",
                text="Explore rooftop solar or a green energy tariff if available in your area.",
                potential_reduction_tonnes=round(results.electricity * 0.5, 2),
            )
        )

    # --- Diet --------------------------------------------------------------
    if inputs.diet_type in {"High Meat Diet", "Mixed Diet"}:
        current_factor = DIET_EMISSION_FACTORS[inputs.diet_type]
        veg_factor = DIET_EMISSION_FACTORS["Vegetarian"]
        weekly_saving_kg = (current_factor - veg_factor) * 2
        annual_saving_tonnes = round(
            (weekly_saving_kg * UNITS.WEEKS_PER_YEAR) / UNITS.KG_PER_TONNE, 2
        )
        recommendations.append(
            Recommendation(
                icon="🥦",
                text="Try eating vegetarian meals twice a week to lower your dietary footprint.",
                potential_reduction_tonnes=max(annual_saving_tonnes, 0),
            )
        )

    # --- Air travel ----------------------------------------------------
    if inputs.international_flights > 0 or inputs.domestic_flights > 2:
        recommendations.append(
            Recommendation(
                icon="✈️",
                text="Reduce non-essential flights, or offset unavoidable air travel through "
                "verified carbon offset programs.",
                potential_reduction_tonnes=round(results.air_travel * 0.3, 2),
            )
        )

    # --- Waste -----------------------------------------------------------
    if inputs.waste_disposal_method == "Landfill":
        recommendations.append(
            Recommendation(
                icon="♻️",
                text="Segregate waste and shift to recycling or composting instead of landfill disposal.",
                potential_reduction_tonnes=round(results.waste * 0.7, 2),
            )
        )
    elif results.waste > 0.05:
        recommendations.append(
            Recommendation(
                icon="🌿",
                text="Start composting organic/kitchen waste to further cut disposal emissions.",
                potential_reduction_tonnes=round(results.waste * 0.2, 2),
            )
        )

    if not recommendations:
        recommendations.append(
            Recommendation(
                icon="🌍",
                text="Your footprint already looks efficient across categories — "
                "keep monitoring and maintaining these habits!",
                potential_reduction_tonnes=0.0,
            )
        )

    recommendations.sort(key=lambda r: r.potential_reduction_tonnes, reverse=True)
    return recommendations


def total_potential_reduction(recommendations: List[Recommendation]) -> float:
    return round(sum(r.potential_reduction_tonnes for r in recommendations), 2)


# =============================================================================
# SECTION 5: CHARTS  (formerly charts.py)
# =============================================================================

CATEGORY_COLORS = {
    "Transportation": "#2E86AB",
    "Electricity": "#F6AE2D",
    "Diet": "#33A02C",
    "Air Travel": "#A23B72",
    "Waste": "#6C757D",
}


def build_emissions_pie_chart(results: EmissionResults) -> go.Figure:
    data = results.as_dict()
    labels = list(data.keys())
    values = list(data.values())
    colors = [CATEGORY_COLORS[label] for label in labels]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                hovertemplate="%{label}: %{value:.2f} t CO₂<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Emissions Share by Category",
        showlegend=True,
        margin=dict(t=50, b=20, l=20, r=20),
        height=380,
    )
    return fig


def build_emissions_bar_chart(results: EmissionResults) -> go.Figure:
    data = results.as_dict()
    labels = list(data.keys())
    values = list(data.values())
    colors = [CATEGORY_COLORS[label] for label in labels]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=[f"{v:.2f}" for v in values],
                textposition="outside",
                hovertemplate="%{x}: %{y:.2f} t CO₂<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Emissions by Category (t CO₂/year)",
        yaxis_title="Tonnes CO₂ / year",
        margin=dict(t=50, b=20, l=20, r=20),
        height=380,
    )
    return fig


def build_benchmark_chart(
    total_emissions: float, benchmark_rows: List[Tuple[str, float, float]]
) -> go.Figure:
    labels = [row[0] for row in benchmark_rows] + ["You"]
    values = [row[1] for row in benchmark_rows] + [total_emissions]
    colors = ["#A9A9A9"] * len(benchmark_rows) + ["#2E86AB"]

    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color=colors,
                text=[f"{v:.2f} t" for v in values],
                textposition="outside",
                hovertemplate="%{y}: %{x:.2f} t CO₂<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Your Footprint vs. National / Global Averages",
        xaxis_title="Tonnes CO₂ / year",
        margin=dict(t=50, b=20, l=20, r=20),
        height=380,
    )
    return fig


# =============================================================================
# SECTION 6: STREAMLIT APP  (formerly app.py)
# =============================================================================

st.set_page_config(
    layout="wide",
    page_title="Personal Carbon Footprint Calculator",
    page_icon="🌍",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .metric-card {
            background-color: rgba(46, 134, 171, 0.08);
            border-radius: 10px;
            padding: 1rem;
            border: 1px solid rgba(46, 134, 171, 0.25);
        }
        .rec-card {
            background-color: rgba(51, 160, 44, 0.07);
            border-left: 4px solid #33A02C;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
        }
        h1, h2, h3 { font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar -----------------------------------------------------------
with st.sidebar:
    st.title("🌍 Carbon Calculator")
    st.caption("A Climate Tech portfolio project")

    st.markdown(
        "Estimate your **annual personal carbon footprint** across five "
        "categories, benchmark it globally, and get tailored recommendations "
        "to reduce it."
    )

    with st.expander("ℹ️ Methodology & Data Sources"):
        st.markdown(
            """
            - Emission factors are illustrative approximations for
              demonstration purposes (see the top of this file for full
              source notes).
            - Electricity uses India's grid average emission intensity.
            - Diet emissions follow patterns from food lifecycle research
              (Poore & Nemecek, 2018).
            - Benchmarks reflect recently reported per-capita national
              averages (Our World in Data / Global Carbon Project).
            """
        )

    with st.expander("🛠️ Built With"):
        st.markdown("- Python\n- Streamlit\n- Plotly\n\n(Single-file build)")

    st.divider()
    st.caption("Built by Atharva · ESG & Sustainability Data Portfolio")

# --- Header --------------------------------------------------------------
st.title("🌍 Personal Carbon Footprint Calculator")
st.markdown(
    "Estimate your **annual CO₂ footprint**, see how it compares globally, "
    "and get personalized suggestions to reduce it."
)
st.divider()

# --- Input section ---------------------------------------------------------
st.header("📝 Your Profile")

country = st.selectbox(
    "🌍 Country",
    options=["India"],
    index=0,
    help="Used to apply the correct electricity grid emission factor.",
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🚗 Transportation", "💡 Electricity", "🍽️ Diet", "✈️ Air Travel", "🗑️ Waste"]
)

with tab1:
    col_a, col_b = st.columns([1, 1])
    with col_a:
        transport_mode = st.selectbox(
            "Primary mode of transport",
            options=list(TRANSPORT_EMISSION_FACTORS.keys()),
            format_func=lambda m: f"{TRANSPORT_ICONS.get(m, '')} {m}",
            help="Choose the mode you use most often for daily commuting.",
        )
    with col_b:
        daily_distance = st.slider(
            "Daily commute distance (km)",
            min_value=0.0,
            max_value=150.0,
            value=10.0,
            step=0.5,
            help="Round-trip distance travelled per day using the selected mode.",
        )

with tab2:
    monthly_electricity = st.slider(
        "Monthly electricity consumption (kWh)",
        min_value=0.0,
        max_value=1500.0,
        value=150.0,
        step=10.0,
        help="Check your monthly electricity bill for this figure.",
    )

with tab3:
    col_c, col_d = st.columns([1, 1])
    with col_c:
        diet_type = st.selectbox(
            "Diet type",
            options=list(DIET_EMISSION_FACTORS.keys()),
            index=4,
            format_func=lambda d: f"{DIET_ICONS.get(d, '')} {d}",
            help="Choose the option that best reflects your typical weekly diet.",
        )
    with col_d:
        meals_per_day = st.number_input(
            "Meals per day",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=1.0,
            help="Average number of main meals you eat per day.",
        )

with tab4:
    col_e, col_f = st.columns([1, 1])
    with col_e:
        domestic_flights = st.number_input(
            "Domestic flights per year", min_value=0, max_value=100, value=0, step=1
        )
    with col_f:
        international_flights = st.number_input(
            "International flights per year", min_value=0, max_value=50, value=0, step=1
        )

with tab5:
    col_g, col_h = st.columns([1, 1])
    with col_g:
        weekly_waste = st.slider(
            "Waste generated per week (kg)",
            min_value=0.0,
            max_value=100.0,
            value=7.0,
            step=0.5,
        )
    with col_h:
        waste_disposal_method = st.selectbox(
            "Primary disposal method",
            options=list(WASTE_EMISSION_FACTORS.keys()),
            format_func=lambda w: f"{WASTE_ICONS.get(w, '')} {w}",
            help="How most of your household waste is disposed of.",
        )

st.divider()
calculate_clicked = st.button(
    "🧮 Calculate My Carbon Footprint", type="primary", use_container_width=True
)

# --- Results section ---------------------------------------------------
if calculate_clicked:
    inputs = UserInputs(
        country=country,
        transport_mode=transport_mode,
        daily_distance_km=daily_distance,
        monthly_electricity_kwh=monthly_electricity,
        diet_type=diet_type,
        meals_per_day=meals_per_day,
        domestic_flights=int(domestic_flights),
        international_flights=int(international_flights),
        weekly_waste_kg=weekly_waste,
        waste_disposal_method=waste_disposal_method,
    )

    results = calculate_all_emissions(inputs)

    st.header("📊 Results Dashboard")

    m1, m2, m3, m4, m5 = st.columns(5)
    for col, (label, icon, value) in zip(
        [m1, m2, m3, m4, m5],
        [
            ("Transportation", "🚗", results.transportation),
            ("Electricity", "💡", results.electricity),
            ("Diet", "🍽️", results.diet),
            ("Air Travel", "✈️", results.air_travel),
            ("Waste", "🗑️", results.waste),
        ],
    ):
        with col:
            st.metric(label=f"{icon} {label}", value=f"{value:.2f} t")

    st.markdown("")
    st.success(f"🌍 **Total Annual Carbon Footprint: {results.total:.2f} tonnes CO₂e/year**")

    st.subheader("📈 Visual Breakdown")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(build_emissions_pie_chart(results), use_container_width=True)
    with chart_col2:
        st.plotly_chart(build_emissions_bar_chart(results), use_container_width=True)

    st.subheader("🌐 Benchmark Comparison")
    benchmark_result = compare_to_benchmark(results.total, reference="India")
    benchmark_rows = get_all_benchmarks_table(results.total)

    status_color = {
        "Below Average": "success",
        "Near Average": "warning",
        "Above Average": "error",
    }[benchmark_result.status]
    getattr(st, status_color)(f"**{benchmark_result.status}** — {benchmark_result.explanation}")

    st.plotly_chart(
        build_benchmark_chart(results.total, benchmark_rows), use_container_width=True
    )

    st.subheader("💡 Personalized Sustainability Recommendations")
    recs = generate_recommendations(inputs, results)
    potential_total = total_potential_reduction(recs)

    for rec in recs:
        st.markdown(
            f"""<div class="rec-card">{rec.icon} <strong>{rec.text}</strong><br>
            <span style="color:#33A02C;">Potential reduction: {rec.potential_reduction_tonnes:.2f} t CO₂/year</span>
            </div>""",
            unsafe_allow_html=True,
        )

    st.info(
        f"🌱 **Total Potential Reduction if all recommendations are adopted: "
        f"{potential_total:.2f} tonnes CO₂/year**"
    )
else:
    st.info("👆 Fill in your details above and click **Calculate My Carbon Footprint** to see your results.")

st.divider()
st.caption(
    "⚠️ Emission factors used in this app are illustrative approximations for demonstration "
    "purposes only. See the top of this file for source notes and update with verified data "
    "before using for formal reporting."
)
