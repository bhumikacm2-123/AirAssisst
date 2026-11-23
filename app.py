
"""
AirAssist - AI-Powered Air Quality Monitoring
and Health Advisory System

Professional Flask Application Server
Version: 3.1
"""

from pathlib import Path
import logging
import math

import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    Response,
)
from flask_cors import CORS

from flask import Flask, render_template
from services.aqi_service import fetch_realtime_aqi
from services.historical_service import (
    get_all_cities,
    get_city_details,
    get_top_polluted_cities,
    compare_multiple_cities,
    get_state_pollution_summary,
    get_historical_tamil_nadu_trends,
    get_raw_records_page,
    get_cleanest_cities,
    get_pollutant_statistics,
    get_filtered_time_series,
    get_all_cities_ranking,
    generate_csv_report,
)
from services.ai_advisory_service import (
    generate_personalized_health_advisory,
)
from rag_chat_service import generate_rag_answer


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
VISUALIZATION_DIR = BASE_DIR / "data" / "visualizations"
MODEL_PATH = BASE_DIR / "models" / "best_pm10_model.pkl"

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)

CORS(app)

app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("AirAssist")

_PM10_MODEL = None


# ============================================================
# ADDITIONAL REAL-TIME AQI CITIES
# ============================================================

ADDITIONAL_CITIES = {
    "davangere": {
        "city": "Davangere",
        "lat": 14.4644,
        "lon": 75.9218,
        "state": "Karnataka",
    },
    "davanagere": {
        "city": "Davangere",
        "lat": 14.4644,
        "lon": 75.9218,
        "state": "Karnataka",
    },
    "bengaluru": {
        "city": "Bengaluru",
        "lat": 12.9716,
        "lon": 77.5946,
        "state": "Karnataka",
    },
    "bangalore": {
        "city": "Bengaluru",
        "lat": 12.9716,
        "lon": 77.5946,
        "state": "Karnataka",
    },
}


# ============================================================
# COMMON RESPONSE AND VALIDATION HELPERS
# ============================================================

def success_response(data=None, message=None, status_code=200):
    """Return a consistent successful JSON response."""

    response = {"status": "success"}

    if message:
        response["message"] = message

    if isinstance(data, dict):
        response.update(data)
    elif data is not None:
        response["data"] = data

    return jsonify(response), status_code


def error_response(message, status_code=400):
    """Return a consistent JSON error response."""

    return jsonify({
        "status": "error",
        "message": str(message),
    }), status_code


def get_json_payload():
    """Read and validate a JSON request body."""

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return None

    return payload


def get_city_coordinates(city_name):
    """
    Find city coordinates using additional supported cities
    first, then the historical city dataset.

    Returns:
        (city_name, latitude, longitude), or None.
    """

    if not isinstance(city_name, str) or not city_name.strip():
        return None

    requested_city = city_name.strip().casefold()

    # Check additional real-time AQI cities first.
    if requested_city in ADDITIONAL_CITIES:
        city = ADDITIONAL_CITIES[requested_city]

        return (
            city["city"],
            city["lat"],
            city["lon"],
        )

    # Check historical dataset for other supported cities.
    try:
        cities = get_all_cities()

        for city in cities:
            if (
                str(city.get("city", "")).strip().casefold()
                == requested_city
            ):
                lat = float(city["lat"])
                lon = float(city["lon"])

                if not (-90 <= lat <= 90):
                    return None

                if not (-180 <= lon <= 180):
                    return None

                return city["city"], lat, lon

    except (KeyError, TypeError, ValueError):
        logger.exception("City coordinate lookup failed.")

    return None


def resolve_location(city_name, lat=None, lon=None):
    """
    Resolve a requested city and optional coordinates.

    If both coordinates are supplied, validate and use them.
    Otherwise, look up the requested city.

    Unknown cities are never silently replaced with another city.
    """

    if (lat is None) != (lon is None):
        raise ValueError(
            "Please provide both latitude and longitude, or neither."
        )

    if lat is not None and lon is not None:

        try:
            lat = float(lat)
            lon = float(lon)

        except (TypeError, ValueError):
            raise ValueError(
                "Latitude and longitude must be numbers."
            )

        if not math.isfinite(lat) or not math.isfinite(lon):
            raise ValueError(
                "Latitude and longitude must be finite numbers."
            )

        if not (-90 <= lat <= 90):
            raise ValueError(
                "Latitude must be between -90 and 90."
            )

        if not (-180 <= lon <= 180):
            raise ValueError(
                "Longitude must be between -180 and 180."
            )

        if not isinstance(city_name, str):
            city_name = "Selected Location"

        return city_name.strip() or "Selected Location", lat, lon

    matched = get_city_coordinates(city_name)

    if matched is None:
        raise ValueError(
            f"City '{city_name}' was not found. "
            "Please select a supported city or provide valid coordinates."
        )

    return matched


def parse_number(
    payload,
    key,
    default,
    minimum=None,
    maximum=None,
):
    """Convert a JSON field into a finite number and validate its range."""

    value = payload.get(key, default)

    try:
        number = float(value)

    except (TypeError, ValueError):
        raise ValueError(f"{key} must be a valid number.")

    if not math.isfinite(number):
        raise ValueError(f"{key} must be a finite number.")

    if minimum is not None and number < minimum:
        raise ValueError(f"{key} must be at least {minimum}.")

    if maximum is not None and number > maximum:
        raise ValueError(f"{key} must not exceed {maximum}.")

    return number


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ============================================================
# REAL-TIME AIR QUALITY APIs
# ============================================================

@app.route("/api/cities", methods=["GET"])
def api_get_cities():

    try:
        cities = get_all_cities()

        if not isinstance(cities, list):
            cities = []

        # Add Davangere to the city list if not already present.
        davangere_exists = any(
            str(city.get("city", "")).strip().casefold()
            in ("davangere", "davanagere")
            for city in cities
            if isinstance(city, dict)
        )

        if not davangere_exists:
            cities.append({
                "city": "Davangere",
                "state": "Karnataka",
                "lat": 14.4644,
                "lon": 75.9218,
            })

        return success_response({
            "total_cities": len(cities),
            "cities": cities,
        })

    except Exception:
        logger.exception("Unable to retrieve city list.")

        return error_response(
            "Unable to load the city list.",
            500,
        )


@app.route("/api/realtime", methods=["GET"])
def api_get_realtime():

    city = request.args.get("city", "Delhi").strip()

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    try:
        city, lat, lon = resolve_location(
            city,
            lat,
            lon,
        )

        data = fetch_realtime_aqi(
            lat=lat,
            lon=lon,
            city_name=city,
        )

        if not isinstance(data, dict):
            logger.error(
                "AQI service returned an unexpected response."
            )

            return error_response(
                "The air-quality service returned an invalid response.",
                502,
            )

        return jsonify(data)

    except ValueError as error:
        return error_response(str(error), 400)

    except Exception:
        logger.exception("Real-time AQI request failed.")

        return error_response(
            "Unable to retrieve air-quality data right now. "
            "Please try again later.",
            503,
        )


# ============================================================
# HISTORICAL AIR QUALITY APIs
# ============================================================

@app.route("/api/historical/top", methods=["GET"])
def api_historical_top():

    pollutant = request.args.get(
        "pollutant",
        "PM2.5",
    ).strip()

    limit = request.args.get(
        "limit",
        default=10,
        type=int,
    )

    if not limit or limit < 1:
        return error_response(
            "Limit must be between 1 and 100."
        )

    limit = min(limit, 100)

    try:
        top_cities = get_top_polluted_cities(
            pollutant=pollutant,
            n=limit,
        )

        return success_response({
            "pollutant": pollutant,
            "limit": limit,
            "data": top_cities,
        })

    except Exception:
        logger.exception(
            "Historical top-cities request failed."
        )

        return error_response(
            "Unable to retrieve top polluted cities.",
            500,
        )


@app.route("/api/historical/compare", methods=["POST"])
def api_historical_compare():

    payload = get_json_payload()

    if payload is None:
        return error_response(
            "Please send a valid JSON request."
        )

    cities = payload.get(
        "cities",
        ["Delhi", "Bengaluru", "Mumbai", "Kolkata"],
    )

    if (
        not isinstance(cities, list)
        or not cities
        or len(cities) > 6
        or not all(
            isinstance(city, str) and city.strip()
            for city in cities
        )
    ):
        return error_response(
            "Please provide a list of 1 to 6 valid city names."
        )

    try:
        comparison = compare_multiple_cities(cities)

        return success_response({
            "comparison": comparison,
        })

    except Exception:
        logger.exception("City comparison failed.")

        return error_response(
            "Unable to compare the selected cities.",
            500,
        )


@app.route(
    "/api/historical/city/<path:city_name>",
    methods=["GET"],
)
def api_historical_city_detail(city_name):

    try:
        details = get_city_details(city_name)

        if not details:
            return error_response(
                f"City '{city_name}' was not found in the historical dataset.",
                404,
            )

        return success_response({
            "data": details,
        })

    except Exception:
        logger.exception(
            "Historical city detail request failed."
        )

        return error_response(
            "Unable to retrieve city details.",
            500,
        )


@app.route("/api/historical/states", methods=["GET"])
def api_historical_states():

    try:
        summary = get_state_pollution_summary()

        return success_response({
            "states": summary,
        })

    except Exception:
        logger.exception(
            "State pollution summary failed."
        )

        return error_response(
            "Unable to retrieve state pollution summary.",
            500,
        )


@app.route(
    "/api/historical/tamil-nadu-trends",
    methods=["GET"],
)
def api_historical_tamil_nadu():

    try:
        trends = get_historical_tamil_nadu_trends()

        return jsonify(trends)

    except Exception:
        logger.exception(
            "Tamil Nadu historical trends failed."
        )

        return error_response(
            "Unable to retrieve historical trends.",
            500,
        )


@app.route("/api/historical/records", methods=["GET"])
def api_historical_records():

    state = request.args.get("state", "").strip()
    city = request.args.get("city", "").strip()
    pollutant = request.args.get("pollutant", "").strip()

    page = request.args.get(
        "page",
        default=1,
        type=int,
    )

    page_size = request.args.get(
        "page_size",
        default=25,
        type=int,
    )

    if page is None or page < 1:
        return error_response(
            "Page must be at least 1."
        )

    if page_size is None or page_size < 1:
        return error_response(
            "Page size must be between 1 and 100."
        )

    page_size = min(page_size, 100)

    try:
        result = get_raw_records_page(
            state=state,
            city=city,
            pollutant=pollutant,
            page=page,
            page_size=page_size,
        )

        return jsonify(result)

    except Exception:
        logger.exception(
            "Historical records request failed."
        )

        return error_response(
            "Unable to retrieve historical records.",
            500,
        )


@app.route("/api/historical/cleanest", methods=["GET"])
def api_historical_cleanest():

    pollutant = request.args.get(
        "pollutant",
        "PM2.5",
    ).strip()

    limit = request.args.get(
        "limit",
        default=10,
        type=int,
    )

    if limit is None or limit < 1:
        return error_response(
            "Limit must be between 1 and 50."
        )

    limit = min(limit, 50)

    try:
        clean_cities = get_cleanest_cities(
            pollutant=pollutant,
            n=limit,
        )

        return success_response({
            "pollutant": pollutant,
            "limit": limit,
            "data": clean_cities,
        })

    except Exception:
        logger.exception(
            "Cleanest cities request failed."
        )

        return error_response(
            "Unable to retrieve cleanest cities.",
            500,
        )


@app.route("/api/historical/statistics", methods=["GET"])
def api_historical_statistics():

    try:
        stats = get_pollutant_statistics()

        return success_response({
            "statistics": stats,
        })

    except Exception:
        logger.exception(
            "Pollutant statistics request failed."
        )

        return error_response(
            "Unable to retrieve pollutant statistics.",
            500,
        )


@app.route(
    "/api/historical/time-series",
    methods=["GET"],
)
def api_historical_time_series():

    city = request.args.get("city", "All").strip()
    month = request.args.get("month", "All").strip()
    area_type = request.args.get("area_type", "All").strip()

    try:
        series = get_filtered_time_series(
            city=city,
            month=month,
            area_type=area_type,
        )

        return jsonify(series)

    except Exception:
        logger.exception(
            "Historical time-series request failed."
        )

        return error_response(
            "Unable to retrieve time-series data.",
            500,
        )


@app.route("/api/historical/rankings", methods=["GET"])
def api_historical_rankings():

    pollutant = request.args.get(
        "pollutant",
        "PM2.5",
    ).strip()

    try:
        rankings = get_all_cities_ranking(
            pollutant=pollutant,
        )

        return success_response({
            "pollutant": pollutant,
            "total_ranked": len(rankings),
            "rankings": rankings,
        })

    except Exception:
        logger.exception(
            "Historical rankings request failed."
        )

        return error_response(
            "Unable to retrieve city rankings.",
            500,
        )


@app.route("/api/historical/export", methods=["GET"])
def api_historical_export():

    report_type = request.args.get(
        "report_type",
        "rankings",
    ).strip()

    try:
        csv_data = generate_csv_report(
            report_type=report_type,
        )

        if not csv_data:
            return error_response(
                "Unknown or unavailable report type.",
                400,
            )

        filename = (
            f"airassist_cpcb_{report_type}_report.csv"
        )

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    except Exception:
        logger.exception("CSV export failed.")

        return error_response(
            "Unable to generate the CSV report.",
            500,
        )


# ============================================================
# VISUALIZATION FILES
# ============================================================

@app.route(
    "/visualizations/<path:filename>",
    methods=["GET"],
)
def serve_visualization(filename):

    if not VISUALIZATION_DIR.exists():
        return error_response(
            "Visualizations directory not found.",
            404,
        )

    try:
        return send_from_directory(
            VISUALIZATION_DIR,
            filename,
            as_attachment=False,
        )

    except Exception:
        logger.exception(
            "Visualization file request failed."
        )

        return error_response(
            "Visualization file not found.",
            404,
        )


# ============================================================
# AI HEALTH ADVISOR API
# ============================================================

@app.route(
    "/api/ai-advisor/query",
    methods=["POST"],
)
def api_ai_advisor():

    payload = get_json_payload()

    if payload is None:
        return error_response(
            "Please send a valid JSON request."
        )

    city = str(
        payload.get("city", "Delhi")
    ).strip()

    persona = str(
        payload.get("persona", "General Adult")
    ).strip()

    user_query = str(
        payload.get("query", "")
    ).strip()

    if not user_query:
        return error_response(
            "Please enter your health question."
        )

    if len(user_query) > 2000:
        return error_response(
            "Your question must be 2000 characters or fewer."
        )

    if not city:
        return error_response(
            "Please select a city."
        )

    if not persona:
        return error_response(
            "Please select a user profile."
        )

    try:
        city, lat, lon = resolve_location(
            city,
            payload.get("lat"),
            payload.get("lon"),
        )

        realtime_data = fetch_realtime_aqi(
            lat=lat,
            lon=lon,
            city_name=city,
        )

        if not isinstance(realtime_data, dict):
            return error_response(
                "Air-quality data is currently unavailable.",
                503,
            )

        metrics = realtime_data.get("metrics") or {}

        if (
            realtime_data.get("status") != "success"
            or not isinstance(metrics, dict)
            or metrics.get("aqi") is None
        ):
            return error_response(
                "A valid AQI reading is unavailable. "
                "The health advisor cannot create a data-based "
                "advisory yet.",
                503,
            )

        aqi = metrics["aqi"]
        pollutants = metrics.get("pollutants") or {}

        advisory = generate_personalized_health_advisory(
            user_persona=persona,
            city=city,
            aqi=aqi,
            pollutants=pollutants,
            user_query=user_query,
        )

        return success_response({
            "advisory": advisory,
            "realtime_context": {
                "city": city,
                "aqi": aqi,
                "category": metrics.get("category"),
                "temperature": (
                    metrics.get("weather") or {}
                ).get("temperature"),
                "humidity": (
                    metrics.get("weather") or {}
                ).get("humidity"),
                "last_updated": realtime_data.get(
                    "last_updated"
                ),
            },
        })

    except ValueError as error:
        return error_response(str(error), 400)

    except Exception:
        logger.exception(
            "AI Health Advisor request failed."
        )

        return error_response(
            "The AI Health Advisor is temporarily unavailable.",
            503,
        )


# ============================================================
# GEMINI RAG CHATBOT API
# ============================================================

@app.route("/api/chat", methods=["POST"])
def api_rag_chat():

    payload = get_json_payload()

    if payload is None:
        return error_response(
            "Please send a valid JSON request."
        )

    question = str(
        payload.get("question")
        or payload.get("query")
        or ""
    ).strip()

    if not question:
        return jsonify({
            "status": "error",
            "answer": "Please enter an air-quality question.",
            "sources": [],
        }), 400

    if len(question) > 2000:
        return jsonify({
            "status": "error",
            "answer": (
                "Your question must be 2000 characters or fewer."
            ),
            "sources": [],
        }), 400

    try:
        result = generate_rag_answer(question)

        if not isinstance(result, dict):
            raise TypeError(
                "Chatbot returned an invalid response."
            )

        status_code = (
            200 if result.get("status") == "success" else 503
        )

        return jsonify({
            "status": result.get("status", "error"),
            "answer": result.get(
                "answer",
                "Sorry, I could not generate an answer.",
            ),
            "sources": result.get("sources", []),
        }), status_code

    except Exception:
        logger.exception(
            "AirAssist chatbot endpoint failed."
        )

        return jsonify({
            "status": "error",
            "answer": (
                "AirAssist chatbot is temporarily unavailable. "
                "Please try again."
            ),
            "sources": [],
        }), 503


# ============================================================
# APPLICATION HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def api_health():

    return success_response({
        "application": "AirAssist",
        "version": "3.1",
        "message": "AirAssist Flask server is running.",
    })


# ============================================================
# MACHINE LEARNING PM10 PREDICTION API
# ============================================================

@app.route(
    "/api/ml/predict-pm10",
    methods=["POST"],
)
def api_predict_pm10():

    global _PM10_MODEL

    payload = get_json_payload()

    if payload is None:
        return error_response(
            "Please send a valid JSON request."
        )

    if not MODEL_PATH.exists():
        return error_response(
            "PM10 ML model file was not found.",
            404,
        )

    try:
        so2 = parse_number(
            payload, "SO2", 12.0, 0, 1000
        )

        no2 = parse_number(
            payload, "NO2", 25.0, 0, 1000
        )

        month = parse_number(
            payload, "Month", 11, 1, 12
        )

        day_of_year = parse_number(
            payload, "DayOfYear", 315, 1, 366
        )

        stn_code = parse_number(
            payload, "StnCode", 768, 0, 100000000
        )

        city = str(
            payload.get("City", "Chennai")
        ).strip()

        if not city or len(city) > 100:
            return error_response(
                "Please provide a valid city name."
            )

        if not month.is_integer():
            return error_response(
                "Month must be a whole number."
            )

        if not day_of_year.is_integer():
            return error_response(
                "DayOfYear must be a whole number."
            )

        if not stn_code.is_integer():
            return error_response(
                "StnCode must be a whole number."
            )

        if _PM10_MODEL is None:
            import joblib

            _PM10_MODEL = joblib.load(MODEL_PATH)

        input_df = pd.DataFrame({
            "SO2": [so2],
            "NO2": [no2],
            "Month": [int(month)],
            "DayOfYear": [int(day_of_year)],
            "City/Town/Village/Area": [city],
            "Stn Code": [int(stn_code)],
        })

        prediction = _PM10_MODEL.predict(input_df)[0]
        prediction = float(prediction)

        if not math.isfinite(prediction):
            raise ValueError(
                "The model returned an invalid prediction."
            )

        return success_response({
            "predicted_pm10": round(prediction, 2),
            "unit": "µg/m³",
            "prediction_type": "Machine learning estimate",
            "inputs": {
                "SO2": so2,
                "NO2": no2,
                "Month": int(month),
                "DayOfYear": int(day_of_year),
                "City": city,
                "StnCode": int(stn_code),
            },
        })

    except ValueError as error:
        return error_response(str(error), 400)

    except Exception:
        logger.exception("PM10 prediction failed.")

        return error_response(
            "Unable to generate a PM10 prediction.",
            500,
        )


# ============================================================
# GLOBAL ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def handle_not_found(error):

    if request.path.startswith("/api/"):
        return error_response(
            "API endpoint not found.",
            404,
        )

    return "Page not found.", 404


@app.errorhandler(405)
def handle_method_not_allowed(error):

    if request.path.startswith("/api/"):
        return error_response(
            "HTTP method not allowed for this endpoint.",
            405,
        )

    return "Method not allowed.", 405


@app.errorhandler(413)
def handle_request_too_large(error):

    return error_response(
        "Request is too large. Maximum allowed size is 2 MB.",
        413,
    )


@app.errorhandler(500)
def handle_internal_error(error):

    logger.exception(
        "Unhandled application error."
    )

    if request.path.startswith("/api/"):
        return error_response(
            "An internal server error occurred.",
            500,
        )

    return "An internal server error occurred.", 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 58)
    print("       AIRASSIST - AI AIR QUALITY & HEALTH SYSTEM")
    print("=" * 58)
    print("       Version: 3.1")
    print("       Gemini RAG Chatbot: Enabled")
    print("       Historical Analysis: Enabled")
    print("       ML PM10 Predictor: Enabled")
    print("       Additional City: Davangere")
    print("       AQI Provider: Open-Meteo")
    print("       Server: http://127.0.0.1:5000")
    print("=" * 58 + "\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
