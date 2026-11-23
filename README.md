# AirAssist – AI-Powered Air Quality Monitoring & Health Advisory System

> **Tagline:** *"Breathe Better. Live Healthier."*

---

## 1. Project Overview

**AirAssist** is an intelligent, full-stack environmental health informatics platform designed specifically for Indian cities. It bridges the critical divide between raw atmospheric air pollution numbers (such as an AQI of 403 in Delhi) and actionable, personalized, clinically grounded health protection.

By combining **genuine real-time atmospheric APIs** (Open-Meteo European CAMS / Copernicus atmospheric model), **authentic historical government datasets from data.gov.in** (Central Pollution Control Board - CPCB), and **Retrieval-Augmented Generation (RAG) AI**, AirAssist transforms complex multi-pollutant metrics into clear behavioral precautions tailored to vulnerable populations (asthmatics, children, elderly, outdoor gig workers, and athletes).

---

## 2. Main Application Modules

### Module 1: Professional Homepage & Brand Experience
* **AirAssist Branding & Navigation:** Dynamic navigation bar with live status indicators and instant tab switching.
* **Tagline:** *"Breathe Better. Live Healthier."*
* **Current Air Quality Overview:** Live snapshot card featuring Delhi (or any searched Indian city) with active CPCB NAQI, dominant pollutant, mini-progress bars, and behavioral advice.
* **Smart Search:** Instant auto-complete search covering all 288 Indian cities and 565 stations from the CPCB dataset, with quick-select chips for major metros (Delhi, Bengaluru, Mumbai, Kolkata, Chennai, Hyderabad, Lucknow, Patna, Pune).
* **Official CPCB NAQI Classification Matrix:** Detailed breakdown of Good (0–50), Satisfactory (51–100), Moderate (101–200), Poor (201–300), Very Poor (301–400), and Severe (401–500+) with official color codes.
* **Key Pillars & How AirAssist Works:** Step-by-step 4-stage pipeline from spatial query to clinical synthesis.

### Module 2: Real-Time Air Quality Dashboard
* **Primary AQI Metric:** Circular dynamic gauge computing official Indian National Air Quality Index (NAQI) using CPCB piecewise linear breakpoints, alongside US EPA AQI comparison.
* **All 6 Regulated Pollutants:**
  * **$PM_{2.5}$** (Fine Particulate Matter) vs. WHO 24-hr limit ($15\ \mu\text{g/m}^3$) & CPCB limit ($60\ \mu\text{g/m}^3$).
  * **$PM_{10}$** (Coarse Particulate Matter) vs. WHO ($45\ \mu\text{g/m}^3$) & CPCB ($100\ \mu\text{g/m}^3$).
  * **$CO$** (Carbon Monoxide) in $\text{mg/m}^3$ vs. CPCB 8-hr standard ($2.0\ \text{mg/m}^3$).
  * **$NO_2$** (Nitrogen Dioxide) vs. WHO ($25\ \mu\text{g/m}^3$) & CPCB ($80\ \mu\text{g/m}^3$).
  * **$SO_2$** (Sulphur Dioxide) vs. WHO ($40\ \mu\text{g/m}^3$) & CPCB ($80\ \mu\text{g/m}^3$).
  * **$O_3$** (Ground-level Ozone) vs. WHO ($100\ \mu\text{g/m}^3$) & CPCB ($100\ \mu\text{g/m}^3$).
* **Meteorological Integration:** Real-time ambient Temperature (°C) and Relative Humidity (%) to evaluate thermal inversion and smog entrapment.
* **24-Hour Forecast Chart:** Interactive Chart.js forecast of $PM_{2.5}, PM_{10}$, and AQI for the next 24 hours.
* **Interactive Station Map:** Leaflet.js interactive map centering on the city with a color-coded AQI circle marker.
* **Authentic Data Guarantee:** Genuine data sourced via Open-Meteo & Copernicus atmospheric reanalysis. No artificial or fake readings generated. Clear error banner if the gateway is unreachable.

### Module 3: Historical Air Quality Analysis (Phase 3: Interactive Charts)
* **Dataset Preservation:** Uses your authentic downloaded data.gov.in CSV files:
  * `data/processed/air_quality_cleaned.csv` (3,737 station records across 288 Indian cities).
  * `data/processed/city_pollution_summary.csv` (Aggregated city pollutant pivot matrix).
  * `data/raw/cpcb_dly_aq_tamil_nadu-2015.csv` (2,302 daily time-series sampling records across 2015).
* **Interactive Filtering System:** Dynamic filters for City (*Chennai, Coimbatore, Madurai, Salem, etc.*), Season/Month (*Winter, Summer, Monsoon, Jan-Dec*), and Zoning Area Type (*Industrial vs. Residential*).
* **Chronological Time-Series Chart:** Multi-pollutant tracking of RSPM/$PM_{10}$, $PM_{2.5}$, $NO_2$, and $SO_2$ across sampling dates.
* **City-Wise Comparison:** Compare any 2 to 5 Indian cities side-by-side with presets for Major Metros, PM2.5 Hotspots, and Tier-1 Urban Centers using grouped bar charts.
* **Top Polluted vs. Cleanest Cities:** Dynamic toggle between the Top 10 Most Polluted Cities and Top 10 Cleanest Cities with sufficient valid monitoring data.
* **12-Month Longitudinal Trends:** Seasonal exposure contrasts (*Winter vs. Summer vs. Monsoon*), and Industrial vs. Residential zoning analysis.
* **Comprehensive National Rankings Table:** Searchable and paginated scorecard of all 288 monitored Indian urban centers with national percentiles and CPCB bands.

### Module 4: Advanced Analytics & Export Center (Phase 4)
* **Authentic Descriptive Statistics:** Detailed statistical breakdown (Count, Mean, Median, Standard Deviation, Min, Max, 90th Percentile) for all 7 regulated pollutants ($PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3, NH_3$).
* **Tamil Nadu Monthly Deep-Dive:** Comprehensive regional case study analyzing peak accumulation months (July & February) and monsoon wash-out scavenging (September drop to 33.1 μg/m³).
* **Automated Data Export:** Download verified CSV reports directly from the platform:
  * `airassist_cpcb_rankings_report.csv` (Complete city rankings with percentiles)
  * `airassist_cpcb_monthly_trends_report.csv` (Longitudinal 12-month data)
  * `airassist_cpcb_statistics_report.csv` (Descriptive statistics summary)

### Module 5: AI Health Advisory & RAG Chatbot
* **Dual RAG Engine:** Supports both Gemini AI via vector store knowledge retrieval (`/api/chat`) and deterministic clinical guideline synthesis (`/api/ai-advisor/query`).
* **Demographic Persona Customization:** Tailored advice for:
  1. *General Healthy Adult*
  2. *Asthmatic / COPD / Respiratory Patient*
  3. *Senior Citizen (65+)*
  4. *Child / School Student / Parent*
  5. *Outdoor / Gig Delivery Worker*
  6. *Runner / Fitness Athlete*
* **Clinical Knowledge Grounding:** References WHO (2021) guidelines, ICMR environmental health bulletins, AIIMS Delhi protocols, and BIS 9473 / N95 respirator standards.
* **Emergency SOS Detector:** Automatically flags acute symptoms (*"chest pain"*, *"cannot breathe"*, *"blue lips"*, *"low oxygen"*) with emergency ambulance notices (108 / 112).

### Module 5: Health Awareness & Clinical Guide
* Detailed guide on PM2.5 vs PM10 alveolar penetration and systemic vascular inflammation.
* Gaseous pollutant toxicology ($NO_2, SO_2, CO, O_3$).
* Mask Guide: Cloth vs. Surgical vs. Certified N95/FFP2 respirators.
* Indoor Air Guide: True HEPA (H13 grade), CADR room sizing, and ionizer warnings.
* Full Vulnerability Action Matrix table across all 6 AQI bands.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.12 / 3.14, Flask 3.1, Flask-CORS |
| **Data Engineering** | Pandas, NumPy, Scikit-Learn, Joblib |
| **Real-Time Data APIs** | Open-Meteo Air Quality & Weather APIs (European CAMS / Copernicus) |
| **Historical Data Sources**| Central Pollution Control Board (CPCB), data.gov.in |
| **AI / NLP Engine** | Google GenAI (Gemini 2.5 Flash), TF-IDF Vector Store, Clinical RAG |
| **Frontend UI / UX** | Responsive HTML5, Modern CSS (Glassmorphism, Navy/Emerald palette) |
| **Visualization & Mapping**| Chart.js 4.4, Leaflet.js 1.9, FontAwesome 6.5 |

---

## 4. How to Run the Application

### Option 1: One-Click Batch Script (Windows)
Double-click:
```
run_app.bat
```

### Option 2: Command Line (PowerShell / Terminal)
```powershell
cd "C:\Users\BHUMIKA C M\OneDrive\Documents\Air Assist"
python app.py
```
Then open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 5. API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Main responsive web application interface |
| `/api/cities` | `GET` | Registry of all 288 Indian cities with station metrics & coordinates |
| `/api/realtime` | `GET` | Real-time CPCB NAQI, pollutants, weather, and 24-hr hourly forecast |
| `/api/historical/top` | `GET` | Top N polluted cities for PM2.5, PM10, NO2, SO2, CO |
| `/api/historical/cleanest` | `GET` | Top N cleanest cities with valid monitoring data |
| `/api/historical/statistics` | `GET` | Descriptive statistics (Mean, Median, Std, P90) for all pollutants |
| `/api/historical/time-series` | `GET` | Filtered chronological time-series (City, Month, Area Type) |
| `/api/historical/rankings` | `GET` | Full national ranking and percentile scorecard for 288 cities |
| `/api/historical/export` | `GET` | Downloadable CSV reports (rankings, monthly trends, statistics) |
| `/api/historical/compare` | `POST` | Side-by-side comparison matrix for selected cities |
| `/api/historical/city/<name>` | `GET` | Station-level and pollutant breakdown for a specific city |
| `/api/historical/states` | `GET` | State-level air quality rankings across India |
| `/api/historical/tamil-nadu-trends` | `GET` | 12-month, seasonal, and zoning historical trends (CPCB 2015) |
| `/api/historical/records` | `GET` | Paginated raw data records with state, city, and pollutant filters |
| `/api/ml/predict-pm10` | `POST` | Machine learning random forest PM10 prediction |
| `/api/ai-advisor/query` | `POST` | Deterministic RAG clinical health advisory |
| `/api/chat` | `POST` | Gemini-powered contextual RAG chatbot |
| `/api/health` | `GET` | Application health and status check |

---

## 6. Project File Structure

```
Air Assist/
├── app.py                     # Primary Flask server with all REST endpoints
├── run_app.bat                # Windows 1-click launcher
├── requirements.txt           # Python dependency specifications
├── README.md                  # Comprehensive documentation
├── clean_data.py              # Preserved: Cleans raw CPCB national data
├── city_analysis.py           # Preserved: Computes city pollution summary
├── visualize_data.py          # Preserved: Matplotlib top 10 PM2.5 plot
├── visualize_pm10.py          # Preserved: Matplotlib top 10 PM10 plot
├── inspect_data.py            # Preserved: Basic environment inspection
├── inspect_historical.py      # Preserved: Inspects Tamil Nadu 2015 dataset
├── test_best_model.py         # Preserved: ML model inference test
├── rag_chat_service.py        # Gemini RAG chatbot service
├── retrieve_knowledge.py      # Vector search over clinical guidelines
├── services/
│   ├── __init__.py
│   ├── aqi_service.py         # Real-time Open-Meteo ingestion & CPCB NAQI
│   ├── historical_service.py  # CPCB data.gov.in data engine
│   └── ai_advisory_service.py # Clinical guidelines & persona advisory
├── models/
│   ├── best_pm10_model.pkl    # Trained PM10 Random Forest Regressor
│   └── pm10_random_forest.pkl # Model weights
├── data/
│   ├── raw/
│   │   ├── Air Assist.csv     # Raw CPCB national dataset
│   │   └── cpcb_dly_aq_tamil_nadu-2015.csv # Raw historical 2015 time series
│   ├── processed/
│   │   ├── air_quality_cleaned.csv     # Cleaned 288-city dataset
│   │   ├── city_pollution_summary.csv  # Pollutant pivot summary
│   │   └── knowledge_chunks.json       # Clinical guidelines chunks
│   ├── vector_store/
│   │   ├── chunks.json
│   │   ├── tfidf_matrix.pkl
│   │   └── tfidf_vectorizer.pkl
│   └── visualizations/        # High-res saved charts from python scripts
│       ├── top_10_pm25_cities.png
│       └── top_10_pm10_cities.png
├── templates/
│   └── index.html             # Full-featured responsive HTML5 single page app
└── static/
    ├── css/
    │   └── style.css          # Navy + Emerald responsive styling (1300+ lines)
    └── js/
        └── app.js             # Interactive controller, Chart.js, Leaflet, Chat
```

---
*Developed for Indian Cities & Public Health Protection &bull; © 2026 AirAssist*
