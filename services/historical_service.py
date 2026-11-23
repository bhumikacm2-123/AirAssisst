"""
AirAssist - Historical Analysis Service
Processes the user's authentic data.gov.in air quality datasets:
1. data/processed/air_quality_cleaned.csv (National CPCB stations snapshot across 288 cities)
2. data/processed/city_pollution_summary.csv (Aggregated pollutant summary table)
3. data/raw/cpcb_dly_aq_tamil_nadu-2015.csv (Historical time-series sampling data)
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
CLEANED_DATA_PATH = BASE_DIR / "data" / "processed" / "air_quality_cleaned.csv"
SUMMARY_DATA_PATH = BASE_DIR / "data" / "processed" / "city_pollution_summary.csv"
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "Air Assist.csv"
TN_2015_PATH = BASE_DIR / "data" / "raw" / "cpcb_dly_aq_tamil_nadu-2015.csv"

# Global data holders for fast access
_DF_CLEANED: Optional[pd.DataFrame] = None
_DF_SUMMARY: Optional[pd.DataFrame] = None
_DF_TN2015: Optional[pd.DataFrame] = None
_CITIES_REGISTRY: Optional[List[Dict[str, Any]]] = None


def load_datasets():
    """Loads and caches datasets into memory."""
    global _DF_CLEANED, _DF_SUMMARY, _DF_TN2015, _CITIES_REGISTRY

    if _DF_CLEANED is None and CLEANED_DATA_PATH.exists():
        _DF_CLEANED = pd.read_csv(CLEANED_DATA_PATH)
        for col in ["latitude", "longitude", "pollutant_min", "pollutant_max", "pollutant_avg"]:
            if col in _DF_CLEANED.columns:
                _DF_CLEANED[col] = pd.to_numeric(_DF_CLEANED[col], errors="coerce")

    if _DF_SUMMARY is None and SUMMARY_DATA_PATH.exists():
        _DF_SUMMARY = pd.read_csv(SUMMARY_DATA_PATH)

    if _DF_TN2015 is None and TN_2015_PATH.exists():
        _DF_TN2015 = pd.read_csv(TN_2015_PATH)
        _DF_TN2015["date"] = pd.to_datetime(_DF_TN2015["Sampling Date"], format="%d-%m-%y", errors="coerce")
        _DF_TN2015["month"] = _DF_TN2015["date"].dt.strftime("%b")
        _DF_TN2015["month_num"] = _DF_TN2015["date"].dt.month
        for col in ["SO2", "NO2", "RSPM/PM10", "PM 2.5"]:
            if col in _DF_TN2015.columns:
                _DF_TN2015[col] = pd.to_numeric(_DF_TN2015[col], errors="coerce")

    # Build comprehensive city registry
    if _CITIES_REGISTRY is None and _DF_CLEANED is not None:
        city_groups = _DF_CLEANED.groupby("city").agg(
            state=("state", "first"),
            lat=("latitude", "mean"),
            lon=("longitude", "mean"),
            stations=("station", "nunique"),
            records=("pollutant_avg", "count")
        ).reset_index()

        # Merge with average PM2.5 and PM10 if present
        pm25_map = (
            _DF_CLEANED[_DF_CLEANED["pollutant_id"] == "PM2.5"]
            .groupby("city")["pollutant_avg"]
            .mean()
            .to_dict()
        )
        pm10_map = (
            _DF_CLEANED[_DF_CLEANED["pollutant_id"] == "PM10"]
            .groupby("city")["pollutant_avg"]
            .mean()
            .to_dict()
        )

        registry = []
        for _, row in city_groups.iterrows():
            c_name = row["city"]
            registry.append({
                "city": c_name,
                "state": row["state"],
                "lat": round(float(row["lat"]), 4) if pd.notnull(row["lat"]) else 20.5937,
                "lon": round(float(row["lon"]), 4) if pd.notnull(row["lon"]) else 78.9629,
                "stations": int(row["stations"]),
                "pm25": round(float(pm25_map.get(c_name, 0)), 1) if pd.notnull(pm25_map.get(c_name)) else None,
                "pm10": round(float(pm10_map.get(c_name, 0)), 1) if pd.notnull(pm10_map.get(c_name)) else None,
            })
        
        # Sort alphabetically
        _CITIES_REGISTRY = sorted(registry, key=lambda x: x["city"])


# Initial load
load_datasets()


def get_all_cities() -> List[Dict[str, Any]]:
    """Returns registry of all 288 cities with coordinates, states, and station metrics."""
    if _CITIES_REGISTRY is None:
        load_datasets()
    return _CITIES_REGISTRY or []


def get_city_details(city_name: str) -> Optional[Dict[str, Any]]:
    """Returns detailed station-by-station and pollutant breakdown for a single city."""
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return None

    subset = _DF_CLEANED[_DF_CLEANED["city"].str.lower() == city_name.strip().lower()]
    if subset.empty:
        return None

    state = subset["state"].iloc[0]
    stations = subset["station"].unique().tolist()
    
    # Pollutant summary
    pollutant_summary = {}
    for pid, group in subset.groupby("pollutant_id"):
        pollutant_summary[pid] = {
            "avg": round(float(group["pollutant_avg"].mean()), 2),
            "min": round(float(group["pollutant_min"].min()), 2) if "pollutant_min" in group else None,
            "max": round(float(group["pollutant_max"].max()), 2) if "pollutant_max" in group else None,
            "readings_count": int(len(group))
        }

    # Station-wise breakdown
    station_breakdown = []
    for st_name, st_group in subset.groupby("station"):
        st_pollutants = {}
        for pid, pgroup in st_group.groupby("pollutant_id"):
            st_pollutants[pid] = round(float(pgroup["pollutant_avg"].mean()), 1)
        
        station_breakdown.append({
            "station": st_name,
            "latitude": round(float(st_group["latitude"].iloc[0]), 4) if pd.notnull(st_group["latitude"].iloc[0]) else None,
            "longitude": round(float(st_group["longitude"].iloc[0]), 4) if pd.notnull(st_group["longitude"].iloc[0]) else None,
            "pollutants": st_pollutants
        })

    return {
        "city": subset["city"].iloc[0],
        "state": state,
        "total_stations": len(stations),
        "last_update": subset["last_update"].iloc[0] if "last_update" in subset else "N/A",
        "pollutants": pollutant_summary,
        "stations": station_breakdown
    }


def get_top_polluted_cities(pollutant: str = "PM2.5", n: int = 10) -> List[Dict[str, Any]]:
    """
    Returns top N polluted cities for the specified pollutant.
    Consistent with visualize_data.py and visualize_pm10.py.
    """
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return []

    sub = _DF_CLEANED[_DF_CLEANED["pollutant_id"].str.upper() == pollutant.strip().upper()]
    if sub.empty:
        return []

    agg = (
        sub.groupby("city")
        .agg(
            state=("state", "first"),
            avg_val=("pollutant_avg", "mean"),
            max_val=("pollutant_max", "max"),
            min_val=("pollutant_min", "min"),
            stations=("station", "nunique")
        )
        .dropna(subset=["avg_val"])
        .sort_values(by="avg_val", ascending=False)
        .head(n)
        .reset_index()
    )

    results = []
    for rank, row in enumerate(agg.itertuples(), start=1):
        results.append({
            "rank": rank,
            "city": row.city,
            "state": row.state,
            "pollutant": pollutant,
            "value": round(float(row.avg_val), 1),
            "max": round(float(row.max_val), 1) if pd.notnull(row.max_val) else None,
            "min": round(float(row.min_val), 1) if pd.notnull(row.min_val) else None,
            "stations": int(row.stations)
        })

    return results


def compare_multiple_cities(city_names: List[str]) -> Dict[str, Any]:
    """
    Compares 2 or more cities across all available pollutants (PM2.5, PM10, NO2, SO2, CO, OZONE, NH3).
    """
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return {"cities": [], "pollutants": [], "matrix": {}}

    clean_names = [c.strip().lower() for c in city_names if c.strip()]
    subset = _DF_CLEANED[_DF_CLEANED["city"].str.lower().isin(clean_names)]

    if subset.empty:
        return {"cities": [], "pollutants": [], "matrix": {}}

    pivot = subset.pivot_table(
        index="city",
        columns="pollutant_id",
        values="pollutant_avg",
        aggfunc="mean"
    ).round(1)

    pollutants = [p for p in ["PM2.5", "PM10", "NO2", "SO2", "CO", "OZONE", "NH3"] if p in pivot.columns]
    
    city_data = {}
    for c in pivot.index:
        city_data[c] = {p: (float(pivot.loc[c, p]) if pd.notnull(pivot.loc[c, p]) else None) for p in pollutants}

    return {
        "cities": list(pivot.index),
        "pollutants": pollutants,
        "matrix": city_data
    }


def get_state_pollution_summary() -> List[Dict[str, Any]]:
    """Returns state-level average pollution metrics across India."""
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return []

    # Get PM2.5 and PM10 state averages
    pm25_df = _DF_CLEANED[_DF_CLEANED["pollutant_id"] == "PM2.5"]
    pm10_df = _DF_CLEANED[_DF_CLEANED["pollutant_id"] == "PM10"]

    state_pm25 = pm25_df.groupby("state")["pollutant_avg"].mean().to_dict()
    state_pm10 = pm10_df.groupby("state")["pollutant_avg"].mean().to_dict()
    state_cities = _DF_CLEANED.groupby("state")["city"].nunique().to_dict()

    summary = []
    for state in sorted(state_cities.keys()):
        summary.append({
            "state": state,
            "cities_monitored": state_cities.get(state, 0),
            "avg_pm25": round(float(state_pm25.get(state, 0)), 1) if state in state_pm25 else None,
            "avg_pm10": round(float(state_pm10.get(state, 0)), 1) if state in state_pm10 else None,
        })

    # Sort descending by PM2.5 where available
    return sorted(summary, key=lambda x: (x["avg_pm25"] or 0), reverse=True)


def get_historical_tamil_nadu_trends() -> Dict[str, Any]:
    """
    Extracts monthly and seasonal historical trends from CPCB 2015 time-series dataset:
    data/raw/cpcb_dly_aq_tamil_nadu-2015.csv
    """
    if _DF_TN2015 is None:
        load_datasets()
    if _DF_TN2015 is None or _DF_TN2015.empty:
        return {"status": "unavailable", "message": "Historical time-series dataset not found."}

    # Monthly trends (ordered Jan - Dec)
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly = _DF_TN2015.groupby("month")[["RSPM/PM10", "SO2", "NO2"]].mean().reindex(months_order).dropna(how="all")

    # City-wise averages across 2015
    city_avg = _DF_TN2015.groupby("City/Town/Village/Area")[["RSPM/PM10", "SO2", "NO2"]].mean().round(1).reset_index()

    # Location type (Industrial vs Residential)
    loc_type = _DF_TN2015.groupby("Type of Location")[["RSPM/PM10", "SO2", "NO2"]].mean().round(1).reset_index()

    # Seasonal classification
    def get_season(month_num):
        if month_num in [12, 1, 2]:
            return "Winter (Dec - Feb)"
        elif month_num in [3, 4, 5, 6]:
            return "Summer (Mar - Jun)"
        else:
            return "Monsoon / Post-Monsoon (Jul - Nov)"

    df_seasonal = _DF_TN2015.copy()
    df_seasonal["season"] = df_seasonal["month_num"].apply(get_season)
    season_avg = df_seasonal.groupby("season")[["RSPM/PM10", "SO2", "NO2"]].mean().round(1).reset_index()

    return {
        "status": "success",
        "dataset_name": "CPCB Official Daily Ambient Air Quality (Tamil Nadu 2015)",
        "total_records": len(_DF_TN2015),
        "monthly_trend": {
            "months": monthly.index.tolist(),
            "pm10": [round(float(v), 1) if pd.notnull(v) else None for v in monthly["RSPM/PM10"]],
            "no2": [round(float(v), 1) if pd.notnull(v) else None for v in monthly["NO2"]],
            "so2": [round(float(v), 1) if pd.notnull(v) else None for v in monthly["SO2"]],
        },
        "city_comparison": city_avg.to_dict(orient="records"),
        "location_type_comparison": loc_type.to_dict(orient="records"),
        "seasonal_comparison": season_avg.to_dict(orient="records")
    }


def get_raw_records_page(state: str = "", city: str = "", pollutant: str = "", page: int = 1, page_size: int = 25) -> Dict[str, Any]:
    """Provides filtered, paginated access to the clean data.gov.in dataset."""
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return {"records": [], "total": 0, "page": page, "pages": 0}

    filtered = _DF_CLEANED
    if state:
        filtered = filtered[filtered["state"].str.lower() == state.strip().lower()]
    if city:
        filtered = filtered[filtered["city"].str.lower() == city.strip().lower()]
    if pollutant:
        filtered = filtered[filtered["pollutant_id"].str.upper() == pollutant.strip().upper()]

    total = len(filtered)
    pages = int(np.ceil(total / page_size)) if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size

    slice_df = filtered.iloc[start:end].copy()
    slice_df = slice_df.replace({np.nan: None})

    return {
        "total": total,
        "page": page,
        "pages": pages,
        "page_size": page_size,
        "records": slice_df.to_dict(orient="records")
    }


def get_cleanest_cities(pollutant: str = "PM2.5", n: int = 10) -> List[Dict[str, Any]]:
    """
    Returns top N cleanest (lowest pollution) cities with sufficient valid data.
    """
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return []

    sub = _DF_CLEANED[_DF_CLEANED["pollutant_id"].str.upper() == pollutant.strip().upper()]
    if sub.empty:
        return []

    agg = (
        sub.groupby("city")
        .agg(
            state=("state", "first"),
            avg_val=("pollutant_avg", "mean"),
            max_val=("pollutant_max", "max"),
            min_val=("pollutant_min", "min"),
            stations=("station", "nunique")
        )
        .dropna(subset=["avg_val"])
        .sort_values(by="avg_val", ascending=True)
        .head(n)
        .reset_index()
    )

    results = []
    for rank, row in enumerate(agg.itertuples(), start=1):
        results.append({
            "rank": rank,
            "city": row.city,
            "state": row.state,
            "pollutant": pollutant,
            "value": round(float(row.avg_val), 1),
            "max": round(float(row.max_val), 1) if pd.notnull(row.max_val) else None,
            "min": round(float(row.min_val), 1) if pd.notnull(row.min_val) else None,
            "stations": int(row.stations)
        })

    return results


def get_pollutant_statistics() -> Dict[str, Any]:
    """
    Computes authentic descriptive statistical summary (Count, Mean, Median, Std, Min, Max, 90th percentile)
    for all pollutants in the CPCB national dataset.
    """
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return {}

    stats = {}
    for pid, group in _DF_CLEANED.groupby("pollutant_id"):
        vals = group["pollutant_avg"].dropna()
        if len(vals) == 0:
            continue
        stats[pid] = {
            "count": int(len(vals)),
            "mean": round(float(vals.mean()), 2),
            "median": round(float(vals.median()), 2),
            "std": round(float(vals.std()), 2) if len(vals) > 1 else 0.0,
            "min": round(float(vals.min()), 2),
            "max": round(float(vals.max()), 2),
            "p90": round(float(vals.quantile(0.9)), 2)
        }

    return stats


def get_filtered_time_series(city: str = "All", month: str = "All", area_type: str = "All") -> Dict[str, Any]:
    """
    Provides dynamic chronological time-series filtering on CPCB 2015 Tamil Nadu dataset.
    Filters by City, Month/Season, and Zoning Area Type.
    """
    if _DF_TN2015 is None:
        load_datasets()
    if _DF_TN2015 is None or _DF_TN2015.empty:
        return {"status": "unavailable", "message": "Time-series data not found."}

    df = _DF_TN2015.copy()

    # City filter
    if city and city.lower() != "all":
        df = df[df["City/Town/Village/Area"].str.lower() == city.strip().lower()]

    # Month filter
    if month and month.lower() != "all":
        if month.isdigit():
            df = df[df["month_num"] == int(month)]
        elif month.lower() in ["winter", "summer", "monsoon"]:
            if month.lower() == "winter":
                df = df[df["month_num"].isin([12, 1, 2])]
            elif month.lower() == "summer":
                df = df[df["month_num"].isin([3, 4, 5, 6])]
            elif month.lower() == "monsoon":
                df = df[df["month_num"].isin([7, 8, 9, 10, 11])]
        else:
            df = df[df["month"].str.lower() == month.strip().lower()[:3]]

    # Area type filter
    if area_type and area_type.lower() != "all":
        df = df[df["Type of Location"].str.lower().str.contains(area_type.strip().lower())]

    if df.empty:
        return {
            "status": "empty",
            "message": "No matching observations found for the selected filter combination.",
            "dates": [],
            "pm10": [],
            "pm25": [],
            "no2": [],
            "so2": []
        }

    # Group by chronological date
    daily = (
        df.groupby("date")
        .agg(
            pm10=("RSPM/PM10", "mean"),
            pm25=("PM 2.5", "mean"),
            no2=("NO2", "mean"),
            so2=("SO2", "mean")
        )
        .sort_index()
    )

    dates = [d.strftime("%d %b") for d in daily.index]
    pm10_vals = [round(float(v), 1) if pd.notnull(v) else None for v in daily["pm10"]]
    pm25_vals = [round(float(v), 1) if pd.notnull(v) else None for v in daily["pm25"]]
    no2_vals = [round(float(v), 1) if pd.notnull(v) else None for v in daily["no2"]]
    so2_vals = [round(float(v), 1) if pd.notnull(v) else None for v in daily["so2"]]

    # Available cities in time-series for filter UI
    available_cities = sorted(_DF_TN2015["City/Town/Village/Area"].dropna().unique().tolist())

    return {
        "status": "success",
        "total_records": len(df),
        "available_cities": available_cities,
        "dates": dates,
        "pm10": pm10_vals,
        "pm25": pm25_vals,
        "no2": no2_vals,
        "so2": so2_vals
    }


def get_all_cities_ranking(pollutant: str = "PM2.5") -> List[Dict[str, Any]]:
    """
    Generates comprehensive national ranking of all monitored cities for the selected pollutant.
    """
    if _DF_CLEANED is None:
        load_datasets()
    if _DF_CLEANED is None:
        return []

    sub = _DF_CLEANED[_DF_CLEANED["pollutant_id"].str.upper() == pollutant.strip().upper()]
    if sub.empty:
        return []

    agg = (
        sub.groupby("city")
        .agg(
            state=("state", "first"),
            avg_val=("pollutant_avg", "mean"),
            max_val=("pollutant_max", "max"),
            min_val=("pollutant_min", "min"),
            stations=("station", "nunique")
        )
        .dropna(subset=["avg_val"])
        .sort_values(by="avg_val", ascending=False)
        .reset_index()
    )

    total_cities = len(agg)
    rankings = []
    for rank, row in enumerate(agg.itertuples(), start=1):
        val = round(float(row.avg_val), 1)
        # Classify band
        if val <= 30:
            category = "Good"
        elif val <= 60:
            category = "Satisfactory"
        elif val <= 90:
            category = "Moderate"
        elif val <= 120:
            category = "Poor"
        elif val <= 250:
            category = "Very Poor"
        else:
            category = "Severe"

        rankings.append({
            "rank": rank,
            "city": row.city,
            "state": row.state,
            "pollutant": pollutant,
            "value": val,
            "category": category,
            "stations": int(row.stations),
            "percentile": round(((total_cities - rank) / total_cities) * 100, 1)
        })

    return rankings


def generate_csv_report(report_type: str = "rankings") -> str:
    """
    Exports clean CSV report for user download.
    Types: 'rankings', 'monthly_trends', 'statistics'.
    """
    if _DF_CLEANED is None:
        load_datasets()

    if report_type == "rankings":
        rankings = get_all_cities_ranking("PM2.5")
        df_out = pd.DataFrame(rankings)
        return df_out.to_csv(index=False)

    elif report_type == "monthly_trends":
        trends = get_historical_tamil_nadu_trends()
        m = trends.get("monthly_trend", {})
        df_out = pd.DataFrame({
            "Month": m.get("months", []),
            "RSPM_PM10_ugm3": m.get("pm10", []),
            "NO2_ugm3": m.get("no2", []),
            "SO2_ugm3": m.get("so2", [])
        })
        return df_out.to_csv(index=False)

    elif report_type == "statistics":
        stats = get_pollutant_statistics()
        rows = []
        for pol, s in stats.items():
            rows.append({
                "Pollutant": pol,
                "Observations": s["count"],
                "Mean": s["mean"],
                "Median": s["median"],
                "StdDev": s["std"],
                "Min": s["min"],
                "Max": s["max"],
                "90th_Percentile": s["p90"]
            })
        df_out = pd.DataFrame(rows)
        return df_out.to_csv(index=False)

    return ""

