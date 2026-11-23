"""
AirAssist - AQI Service
Fetches genuine real-time air quality & weather data from Open-Meteo API
and calculates CPCB Indian National Air Quality Index (NAQI) alongside US EPA AQI.
"""

import time
import requests
from typing import Dict, Any, Optional, Tuple

# In-memory cache for API calls: key -> (timestamp, data)
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 900  # 15 minutes


def calculate_cpcb_sub_index(conc: float, pollutant: str) -> Optional[float]:
    """
    Computes the CPCB Sub-Index for a given pollutant concentration
    using official Indian NAQI piecewise linear breakpoints.
    """
    if conc is None or conc < 0:
        return None

    # Official CPCB Breakpoints: (B_lo, B_hi, I_lo, I_hi)
    breakpoints = {
        "PM2.5": [
            (0, 30, 0, 50),
            (31, 60, 51, 100),
            (61, 90, 101, 200),
            (91, 120, 201, 300),
            (121, 250, 301, 400),
            (250, 500, 401, 500),
        ],
        "PM10": [
            (0, 50, 0, 50),
            (51, 100, 51, 100),
            (101, 250, 101, 200),
            (251, 350, 201, 300),
            (351, 430, 301, 400),
            (430, 600, 401, 500),
        ],
        "NO2": [
            (0, 40, 0, 50),
            (41, 80, 51, 100),
            (81, 180, 101, 200),
            (181, 280, 201, 300),
            (281, 400, 301, 400),
            (400, 800, 401, 500),
        ],
        "SO2": [
            (0, 40, 0, 50),
            (41, 80, 51, 100),
            (81, 380, 101, 200),
            (381, 800, 201, 300),
            (801, 1600, 301, 400),
            (1600, 2400, 401, 500),
        ],
        "CO": [
            (0, 1.0, 0, 50),
            (1.1, 2.0, 51, 100),
            (2.1, 10.0, 101, 200),
            (10.1, 17.0, 201, 300),
            (17.1, 34.0, 301, 400),
            (34.0, 60.0, 401, 500),
        ],
        "O3": [
            (0, 50, 0, 50),
            (51, 100, 51, 100),
            (101, 168, 101, 200),
            (169, 208, 201, 300),
            (209, 748, 301, 400),
            (748, 1000, 401, 500),
        ],
    }

    if pollutant not in breakpoints:
        return None

    # Handle concentrations above highest defined limit
    bp_list = breakpoints[pollutant]
    if conc > bp_list[-1][1]:
        return 500.0

    for b_lo, b_hi, i_lo, i_hi in bp_list:
        if b_lo <= conc <= b_hi:
            if b_hi == b_lo:
                return float(i_lo)
            sub_index = ((i_hi - i_lo) / (b_hi - b_lo)) * (conc - b_lo) + i_lo
            return round(sub_index, 1)

    return None


def get_aqi_category_info(aqi_value: float) -> Dict[str, str]:
    """
    Returns official Indian CPCB NAQI classification, color codes,
    health descriptor, and recommended general precautions.
    """
    if aqi_value is None or aqi_value < 0:
        return {
            "category": "Unknown",
            "color": "#94a3b8",
            "bg_color": "#f1f5f9",
            "text_color": "#475569",
            "health_impact": "Air quality data currently unavailable.",
            "advisory": "Check back shortly or verify station connectivity.",
            "badge_class": "badge-unknown",
        }

    val = round(aqi_value)
    if val <= 50:
        return {
            "category": "Good",
            "color": "#10b981",
            "bg_color": "rgba(16, 185, 129, 0.12)",
            "text_color": "#065f46",
            "health_impact": "Minimal health impact. Air quality is considered satisfactory.",
            "advisory": "Ideal air for outdoor activities, jogging, and natural ventilation.",
            "badge_class": "badge-good",
        }
    elif val <= 100:
        return {
            "category": "Satisfactory",
            "color": "#84cc16",
            "bg_color": "rgba(132, 204, 22, 0.12)",
            "text_color": "#3f6212",
            "health_impact": "Minor breathing discomfort to sensitive people.",
            "advisory": "Safe for general population; exceptionally sensitive people should observe symptoms.",
            "badge_class": "badge-satisfactory",
        }
    elif val <= 200:
        return {
            "category": "Moderate",
            "color": "#eab308",
            "bg_color": "rgba(234, 179, 8, 0.12)",
            "text_color": "#854d0e",
            "health_impact": "Breathing discomfort to people with lung disease, asthma, and heart diseases.",
            "advisory": "Reduce prolonged outdoor exertion if experiencing coughing or throat irritation.",
            "badge_class": "badge-moderate",
        }
    elif val <= 300:
        return {
            "category": "Poor",
            "color": "#f97316",
            "bg_color": "rgba(249, 115, 22, 0.12)",
            "text_color": "#9a3412",
            "health_impact": "Breathing discomfort to most people on prolonged exposure.",
            "advisory": "Wear N95/FFP2 masks outdoors; asthmatics should keep inhalers handy; avoid morning runs.",
            "badge_class": "badge-poor",
        }
    elif val <= 400:
        return {
            "category": "Very Poor",
            "color": "#ef4444",
            "bg_color": "rgba(239, 68, 68, 0.12)",
            "text_color": "#991b1b",
            "health_impact": "Respiratory illness on prolonged exposure. Pronounced effect on people with lung/heart disease.",
            "advisory": "Keep windows closed; run HEPA air purifiers; vulnerable individuals must remain indoors.",
            "badge_class": "badge-very-poor",
        }
    else:
        return {
            "category": "Severe",
            "color": "#7c2d12",
            "bg_color": "rgba(124, 45, 18, 0.15)",
            "text_color": "#7c2d12",
            "health_impact": "Affects healthy people and seriously impacts those with existing diseases.",
            "advisory": "Health emergency. Avoid all outdoor physical activity. Keep doors sealed. Seek medical attention if experiencing respiratory distress.",
            "badge_class": "badge-severe",
        }


def fetch_realtime_aqi(lat: float, lon: float, city_name: str = "") -> Dict[str, Any]:
    """
    Fetches real-time air quality and weather metrics from Open-Meteo APIs.
    Returns complete pollutant breakdown, CPCB NAQI, US AQI, temperature,
    humidity, 24h hourly forecast, and validation metadata.
    """
    cache_key = f"{lat:.3f}_{lon:.3f}"
    now = time.time()

    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    # Real-time Air Quality API URL
    aq_url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi,european_aqi"
        "&hourly=pm10,pm2_5,us_aqi,nitrogen_dioxide,ozone"
        "&forecast_days=2&timezone=auto"
    )

    # Real-time Weather API URL (Temperature and Humidity)
    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,weather_code"
        "&timezone=auto"
    )

    try:
        aq_resp = requests.get(aq_url, timeout=7)
        weather_resp = requests.get(weather_url, timeout=7)

        if aq_resp.status_code != 200:
            return {
                "status": "unavailable",
                "message": f"Air Quality API returned status {aq_resp.status_code}",
                "city": city_name,
                "latitude": lat,
                "longitude": lon,
            }

        aq_json = aq_resp.json()
        current_aq = aq_json.get("current", {})

        weather_json = weather_resp.json() if weather_resp.status_code == 200 else {}
        current_weather = weather_json.get("current", {})

        # Extract measurements
        pm25 = current_aq.get("pm2_5")
        pm10 = current_aq.get("pm10")
        co_ugm3 = current_aq.get("carbon_monoxide")  # in μg/m³
        no2 = current_aq.get("nitrogen_dioxide")
        so2 = current_aq.get("sulphur_dioxide")
        o3 = current_aq.get("ozone")
        us_aqi = current_aq.get("us_aqi")

        # Convert CO from μg/m³ to mg/m³ for Indian CPCB standard (1 mg/m³ = 1000 μg/m³)
        co_mgm3 = round(co_ugm3 / 1000.0, 2) if co_ugm3 is not None else None

        # Compute CPCB sub-indices
        sub_indices = {}
        if pm25 is not None:
            sub_indices["PM2.5"] = calculate_cpcb_sub_index(pm25, "PM2.5")
        if pm10 is not None:
            sub_indices["PM10"] = calculate_cpcb_sub_index(pm10, "PM10")
        if no2 is not None:
            sub_indices["NO2"] = calculate_cpcb_sub_index(no2, "NO2")
        if so2 is not None:
            sub_indices["SO2"] = calculate_cpcb_sub_index(so2, "SO2")
        if co_mgm3 is not None:
            sub_indices["CO"] = calculate_cpcb_sub_index(co_mgm3, "CO")
        if o3 is not None:
            sub_indices["O3"] = calculate_cpcb_sub_index(o3, "O3")

        # Prominent pollutant and overall Indian NAQI
        valid_sub = {k: v for k, v in sub_indices.items() if v is not None}
        if valid_sub:
            prominent_pollutant = max(valid_sub, key=valid_sub.get)
            cpcb_naqi = round(valid_sub[prominent_pollutant])
        else:
            prominent_pollutant = "PM2.5"
            cpcb_naqi = us_aqi if us_aqi is not None else 100

        # Category information
        category_info = get_aqi_category_info(cpcb_naqi)

        # 24-hour hourly trend
        hourly = aq_json.get("hourly", {})
        times = hourly.get("time", [])[:24]
        h_pm25 = hourly.get("pm2_5", [])[:24]
        h_pm10 = hourly.get("pm10", [])[:24]
        h_aqi = hourly.get("us_aqi", [])[:24]

        # Structure payload
        result = {
            "status": "success",
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "last_updated": current_aq.get("time", "Real-Time Live"),
            "data_source": "Open-Meteo European CAMS / Copernicus & Ground Sensor Interpolation",
            "metrics": {
                "aqi": cpcb_naqi,
                "us_aqi": us_aqi,
                "prominent_pollutant": prominent_pollutant,
                "category": category_info["category"],
                "color": category_info["color"],
                "bg_color": category_info["bg_color"],
                "text_color": category_info["text_color"],
                "health_impact": category_info["health_impact"],
                "advisory": category_info["advisory"],
                "badge_class": category_info["badge_class"],
                "pollutants": {
                    "pm25": {
                        "value": pm25,
                        "unit": "μg/m³",
                        "who_limit": 15.0,
                        "cpcb_limit": 60.0,
                        "sub_index": sub_indices.get("PM2.5"),
                    },
                    "pm10": {
                        "value": pm10,
                        "unit": "μg/m³",
                        "who_limit": 45.0,
                        "cpcb_limit": 100.0,
                        "sub_index": sub_indices.get("PM10"),
                    },
                    "co": {
                        "value": co_mgm3,
                        "raw_ugm3": co_ugm3,
                        "unit": "mg/m³",
                        "cpcb_limit": 2.0,
                        "sub_index": sub_indices.get("CO"),
                    },
                    "no2": {
                        "value": no2,
                        "unit": "μg/m³",
                        "who_limit": 25.0,
                        "cpcb_limit": 80.0,
                        "sub_index": sub_indices.get("NO2"),
                    },
                    "so2": {
                        "value": so2,
                        "unit": "μg/m³",
                        "who_limit": 40.0,
                        "cpcb_limit": 80.0,
                        "sub_index": sub_indices.get("SO2"),
                    },
                    "o3": {
                        "value": o3,
                        "unit": "μg/m³",
                        "who_limit": 100.0,
                        "cpcb_limit": 100.0,
                        "sub_index": sub_indices.get("O3"),
                    },
                },
                "weather": {
                    "temperature": current_weather.get("temperature_2m"),
                    "humidity": current_weather.get("relative_humidity_2m"),
                    "unit_temp": "°C",
                    "unit_humidity": "%",
                },
            },
            "hourly_forecast": {
                "times": [t.split("T")[-1] for t in times],
                "pm25": h_pm25,
                "pm10": h_pm10,
                "aqi": h_aqi,
            },
        }

        # Cache valid response
        _CACHE[cache_key] = (now, result)
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unable to reach live sensor gateway: {str(e)}",
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
        }
