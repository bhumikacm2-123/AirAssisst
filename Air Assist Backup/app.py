
"""
AirAssist – AI-Powered Air Quality Monitoring
and Health Advisory System

Main Flask Application Server
"""

from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory
)
from flask_cors import CORS

from services.aqi_service import fetch_realtime_aqi
from services.historical_service import (
    get_all_cities,
    get_city_details,
    get_top_polluted_cities,
    compare_multiple_cities,
    get_state_pollution_summary,
    get_historical_tamil_nadu_trends,
    get_raw_records_page,
)
from services.ai_advisory_service import (
    generate_personalized_health_advisory
)
from rag_chat_service import generate_rag_answer


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

CORS(app)

BASE_DIR = Path(__file__).resolve().parent
VISUALIZATION_DIR = BASE_DIR / "data" / "visualizations"


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# REAL-TIME AIR QUALITY API
# ============================================================

@app.route("/api/cities", methods=["GET"])
def api_get_cities():

    cities = get_all_cities()

    return jsonify({
        "status": "success",
        "total_cities": len(cities),
        "cities": cities
    })


@app.route("/api/realtime", methods=["GET"])
def api_get_realtime():

    city = request.args.get("city", "Delhi").strip()

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    if lat is None or lon is None:

        cities = get_all_cities()

        matched = next(
            (
                c for c in cities
                if c["city"].lower() == city.lower()
            ),
            None
        )

        if matched:

            lat = matched["lat"]
            lon = matched["lon"]
            city = matched["city"]

        else:

            lat = 28.6139
            lon = 77.2090
            city = "Delhi"

    data = fetch_realtime_aqi(
        lat=lat,
        lon=lon,
        city_name=city
    )

    return jsonify(data)


# ============================================================
# HISTORICAL AIR QUALITY API
# ============================================================

@app.route("/api/historical/top", methods=["GET"])
def api_historical_top():

    pollutant = request.args.get("pollutant", "PM2.5")

    limit = request.args.get(
        "limit",
        default=10,
        type=int
    )

    limit = max(1, min(limit, 100))

    top_cities = get_top_polluted_cities(
        pollutant=pollutant,
        n=limit
    )

    return jsonify({
        "status": "success",
        "pollutant": pollutant,
        "limit": limit,
        "data": top_cities
    })


@app.route("/api/historical/compare", methods=["POST"])
def api_historical_compare():

    payload = request.get_json(silent=True) or {}

    cities = payload.get(
        "cities",
        ["Delhi", "Bengaluru", "Mumbai", "Kolkata"]
    )

    if not isinstance(cities, list) or not cities:

        return jsonify({
            "status": "error",
            "message": "Please provide a valid list of cities."
        }), 400

    comparison = compare_multiple_cities(cities[:6])

    return jsonify({
        "status": "success",
        "comparison": comparison
    })


@app.route(
    "/api/historical/city/<path:city_name>",
    methods=["GET"]
)
def api_historical_city_detail(city_name):

    details = get_city_details(city_name)

    if not details:

        return jsonify({
            "status": "not_found",
            "message": f"City '{city_name}' not found in dataset."
        }), 404

    return jsonify({
        "status": "success",
        "data": details
    })


@app.route("/api/historical/states", methods=["GET"])
def api_historical_states():

    summary = get_state_pollution_summary()

    return jsonify({
        "status": "success",
        "states": summary
    })


@app.route(
    "/api/historical/tamil-nadu-trends",
    methods=["GET"]
)
def api_historical_tamil_nadu():

    trends = get_historical_tamil_nadu_trends()

    return jsonify(trends)


@app.route("/api/historical/records", methods=["GET"])
def api_historical_records():

    state = request.args.get("state", "").strip()
    city = request.args.get("city", "").strip()
    pollutant = request.args.get("pollutant", "").strip()

    page = request.args.get(
        "page",
        default=1,
        type=int
    )

    page_size = request.args.get(
        "page_size",
        default=25,
        type=int
    )

    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    result = get_raw_records_page(
        state=state,
        city=city,
        pollutant=pollutant,
        page=page,
        page_size=page_size
    )

    return jsonify(result)


# ============================================================
# VISUALIZATION FILES
# ============================================================

@app.route("/visualizations/<filename>")
def serve_visualization(filename):

    if VISUALIZATION_DIR.exists():

        return send_from_directory(
            VISUALIZATION_DIR,
            filename
        )

    return jsonify({
        "error": "Visualizations directory not found."
    }), 404


# ============================================================
# AI HEALTH ADVISOR API
# ============================================================

@app.route("/api/ai-advisor/query", methods=["POST"])
def api_ai_advisor():

    payload = request.get_json(silent=True) or {}

    city = str(
        payload.get("city", "Delhi")
    ).strip()

    persona = str(
        payload.get("persona", "General Adult")
    ).strip()

    user_query = str(
        payload.get("query", "")
    ).strip()

    lat = payload.get("lat")
    lon = payload.get("lon")

    if not city:
        city = "Delhi"

    if lat is None or lon is None:

        cities = get_all_cities()

        matched = next(
            (
                c for c in cities
                if c["city"].lower() == city.lower()
            ),
            None
        )

        if matched:

            lat = matched["lat"]
            lon = matched["lon"]

        else:

            lat = 28.6139
            lon = 77.2090
            city = "Delhi"

    realtime_data = fetch_realtime_aqi(
        lat=lat,
        lon=lon,
        city_name=city
    )

    metrics = realtime_data.get("metrics", {})

    aqi = metrics.get("aqi", 150)
    pollutants = metrics.get("pollutants", {})

    advisory = generate_personalized_health_advisory(
        user_persona=persona,
        city=city,
        aqi=aqi,
        pollutants=pollutants,
        user_query=user_query
    )

    return jsonify({
        "status": "success",
        "advisory": advisory,
        "realtime_context": {
            "city": city,
            "aqi": aqi,
            "category": metrics.get("category"),
            "temperature": metrics.get(
                "weather", {}
            ).get("temperature"),
            "humidity": metrics.get(
                "weather", {}
            ).get("humidity"),
            "last_updated": realtime_data.get("last_updated")
        }
    })


# ============================================================
# GEMINI POWERED RAG CHATBOT API
# ============================================================

@app.route("/api/chat", methods=["POST"])
def api_rag_chat():

    payload = request.get_json(silent=True) or {}

    question = str(
        payload.get("question", "")
    ).strip()

    # Also accept "query" for compatibility
    if not question:
        question = str(
            payload.get("query", "")
        ).strip()

    if not question:

        return jsonify({
            "status": "error",
            "answer": "Please enter an air-quality question.",
            "sources": []
        }), 400

    try:

        result = generate_rag_answer(question)

        status_code = (
            200 if result.get("status") == "success"
            else 503
        )

        return jsonify({
            "status": result.get("status", "error"),
            "answer": result.get(
                "answer",
                "Sorry, I could not generate an answer."
            ),
            "sources": result.get("sources", [])
        }), status_code

    except Exception as error:

        app.logger.exception(
            "AirAssist chatbot endpoint error"
        )

        return jsonify({
            "status": "error",
            "answer": (
                "AirAssist chatbot is temporarily unavailable. "
                "Please try again."
            ),
            "sources": []
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def api_health():

    return jsonify({
        "status": "success",
        "application": "AirAssist",
        "message": "AirAssist Flask server is running."
    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("\n=======================================================")
    print("   AIRASSIST – AI AIR QUALITY & HEALTH ADVISORY SYSTEM")
    print("=======================================================")
    print("   Gemini RAG Chatbot: Enabled")
    print("   Server: http://127.0.0.1:5000")
    print("=======================================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
