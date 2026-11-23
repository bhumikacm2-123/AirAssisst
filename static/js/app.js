/**
 * AirAssist – Modern Environmental Dashboard Controller
 * Full Frontend Integration for Phase 1, 2, 3 & 4:
 * - Real-Time Sensor Telemetry & Gauge Meters
 * - Phase 3: Interactive Historical Time-Series Charts & Filters (CPCB 2015)
 * - Phase 4: Advanced Environmental Analytics, Descriptive Statistics,
 *   Top 10 Polluted vs Cleanest Cities, National Rankings, and CSV Reports.
 */

// Global Application State
const AppState = {
  currentCity: "Delhi",
  currentLat: 28.6139,
  currentLon: 77.2090,
  currentPersona: "General Adult",
  citiesRegistry: [],
  realtimeData: null,
  compareCities: ["Delhi", "Bengaluru", "Mumbai", "Kolkata"],
  currentLeaderboardPollutant: "PM2.5",
  leaderboardMode: "polluted", // "polluted" or "cleanest"
  rankingsData: [],
  filteredRankings: [],
  rankPage: 1,
  rankPageSize: 15,
  rankTotalPages: 1,
  isChatLoading: false
};

// Chart.js Instances
let forecastChartInstance = null;
let compareParticulateChartInstance = null;
let compareGasesChartInstance = null;
let leaderboardChartInstance = null;
let histAqiTrendChartInstance = null;
let monthlyTrendChartInstance = null;
let seasonalChartInstance = null;
let zoningChartInstance = null;

// Leaflet Map Instance
let leafletMap = null;
let mapMarker = null;
let mapCircle = null;


// =========================================================
// 1. INITIALIZATION ON DOM READY
// =========================================================
document.addEventListener("DOMContentLoaded", async () => {
  console.log("AirAssist Dashboard initializing with Phase 3 & 4 features...");

  // 1. Ingest Indian cities registry from CPCB dataset
  await loadCitiesRegistry();

  // 2. Fetch initial real-time AQI & pollutants for Delhi
  await refreshRealtimeData();

  // 3. Setup city autocomplete search
  setupSearchAutocomplete();

  // 4. Initialize Historical, Comparison, Analytics, and ML views
  initHistoricalViews();

  console.log("AirAssist Dashboard fully initialized!");
});


// =========================================================
// 2. SIDEBAR NAVIGATION & VIEW SWITCHER
// =========================================================
function switchNavTab(tabName) {
  // Update sidebar buttons
  document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.tab === tabName);
  });

  // Update content view visibility
  document.querySelectorAll(".content-view").forEach(view => {
    view.classList.toggle("active", view.id === `view-${tabName}`);
  });

  // Close mobile sidebar if open
  closeSidebarOnMobile();

  // Handle Chart Resizing & Lazy Ingestion
  if (tabName === "dashboard") {
    setTimeout(() => {
      if (forecastChartInstance) forecastChartInstance.resize();
      if (leafletMap) leafletMap.invalidateSize();
    }, 150);
  } else if (tabName === "historical") {
    setTimeout(() => {
      if (histAqiTrendChartInstance) histAqiTrendChartInstance.resize();
      if (monthlyTrendChartInstance) monthlyTrendChartInstance.resize();
      if (seasonalChartInstance) seasonalChartInstance.resize();
      if (zoningChartInstance) zoningChartInstance.resize();
    }, 150);
  } else if (tabName === "leaderboard") {
    setTimeout(() => {
      if (leaderboardChartInstance) leaderboardChartInstance.resize();
    }, 150);
  } else if (tabName === "comparison") {
    setTimeout(() => {
      if (compareParticulateChartInstance) compareParticulateChartInstance.resize();
      if (compareGasesChartInstance) compareGasesChartInstance.resize();
    }, 150);
  } else if (tabName === "analytics") {
    loadAdvancedAnalytics();
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.classList.toggle("sidebar-open");
  }
}

function closeSidebarOnMobile() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar && window.innerWidth <= 860) {
    sidebar.classList.remove("sidebar-open");
  }
}


// =========================================================
// 3. CITY REGISTRY & AUTOCOMPLETE
// =========================================================
async function loadCitiesRegistry() {
  try {
    const resp = await fetch("/api/cities");
    const json = await resp.json();
    if (json.status === "success" && Array.isArray(json.cities)) {
      AppState.citiesRegistry = json.cities;
    }
  } catch (e) {
    console.error("Failed to load cities registry:", e);
  }
}

function setupSearchAutocomplete() {
  const input = document.getElementById("globalCityInput");
  const dropdown = document.getElementById("cityDropdownList");

  if (!input || !dropdown) return;

  input.addEventListener("input", (e) => {
    const term = e.target.value.trim().toLowerCase();
    if (term.length === 0) {
      dropdown.classList.add("hidden");
      dropdown.innerHTML = "";
      return;
    }

    const matches = AppState.citiesRegistry.filter(c =>
      c.city.toLowerCase().includes(term) || (c.state && c.state.toLowerCase().includes(term))
    ).slice(0, 10);

    if (matches.length === 0) {
      dropdown.innerHTML = `<div class="dropdown-item muted">No matching Indian city found</div>`;
      dropdown.classList.remove("hidden");
      return;
    }

    dropdown.innerHTML = matches.map(c => `
      <div class="dropdown-item" onclick="selectCityByName('${c.city}', ${c.lat}, ${c.lon})">
        <div class="di-main"><i class="fa-solid fa-location-dot"></i> <strong>${c.city}</strong></div>
        <div class="di-sub">${c.state || "India"} &bull; ${c.stations} Station(s)</div>
      </div>
    `).join("");

    dropdown.classList.remove("hidden");
  });

  // Close on outside click
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".header-city-search") && dropdown) {
      dropdown.classList.add("hidden");
    }
    if (!e.target.closest(".persona-dropdown-wrap")) {
      const pMenu = document.getElementById("personaMenu");
      if (pMenu) pMenu.classList.add("hidden");
    }
  });
}

function selectCityByName(cityName, lat = null, lon = null) {
  const matched = AppState.citiesRegistry.find(c => c.city.toLowerCase() === cityName.toLowerCase());

  if (matched) {
    AppState.currentCity = matched.city;
    AppState.currentLat = matched.lat;
    AppState.currentLon = matched.lon;
  } else {
    AppState.currentCity = cityName;
    if (lat !== null && lon !== null) {
      AppState.currentLat = lat;
      AppState.currentLon = lon;
    }
  }

  const input = document.getElementById("globalCityInput");
  if (input) input.value = AppState.currentCity;

  const dropdown = document.getElementById("cityDropdownList");
  if (dropdown) dropdown.classList.add("hidden");

  refreshRealtimeData();
}


// =========================================================
// 4. REAL-TIME AIR QUALITY & POLLUTANT CARDS
// =========================================================
async function refreshRealtimeData() {
  const refreshIcon = document.getElementById("refreshIcon");
  if (refreshIcon) refreshIcon.classList.add("fa-spin");

  const errorAlert = document.getElementById("rtErrorAlert");
  if (errorAlert) errorAlert.classList.add("hidden");

  try {
    const url = `/api/realtime?city=${encodeURIComponent(AppState.currentCity)}&lat=${AppState.currentLat}&lon=${AppState.currentLon}`;
    const resp = await fetch(url);
    const data = await resp.json();

    if (data.status === "success" && data.metrics) {
      AppState.realtimeData = data;
      renderRealtimeMetrics(data);
      updateSidebarWidget(data);
      updateChatbotContext(data);
    } else {
      if (errorAlert) {
        document.getElementById("rtErrorMessage").textContent = data.message || "Live sensor data temporarily unavailable.";
        errorAlert.classList.remove("hidden");
      }
    }
  } catch (err) {
    console.error("Real-time fetch error:", err);
    if (errorAlert) {
      document.getElementById("rtErrorMessage").textContent = "Unable to connect to live sensor gateway.";
      errorAlert.classList.remove("hidden");
    }
  } finally {
    if (refreshIcon) refreshIcon.classList.remove("fa-spin");
  }
}

function renderRealtimeMetrics(data) {
  const m = data.metrics;
  const pols = m.pollutants;
  const weather = m.weather;

  const cityTitle = document.getElementById("rtCityTitle");
  if (cityTitle) cityTitle.textContent = `${data.city}, India`;

  const timestamp = document.getElementById("rtTimestamp");
  if (timestamp) timestamp.textContent = `Updated: ${data.last_updated || "Live"}`;

  const aqiCircle = document.getElementById("rtAqiCircle");
  const aqiValue = document.getElementById("rtAqiValue");
  const tierBadge = document.getElementById("rtTierBadge");
  const promPol = document.getElementById("rtProminentPollutant");
  const usAqi = document.getElementById("rtUsAqi");
  const healthImpact = document.getElementById("rtHealthImpact");
  const advisory = document.getElementById("rtAdvisoryText");

  if (aqiValue) aqiValue.textContent = m.aqi;
  if (aqiCircle) {
    aqiCircle.style.borderColor = m.color;
    aqiCircle.style.boxShadow = `0 0 25px ${m.color}35`;
  }
  if (tierBadge) {
    tierBadge.textContent = m.category;
    tierBadge.style.backgroundColor = m.color;
  }
  if (promPol) promPol.textContent = `${m.prominent_pollutant || "PM2.5"} Dominant`;
  if (usAqi) usAqi.textContent = m.us_aqi !== null ? m.us_aqi : "--";
  if (healthImpact) healthImpact.textContent = m.health_impact;
  if (advisory) advisory.innerHTML = `<i class="fa-solid fa-stethoscope"></i> <span><strong>Clinical Advisory:</strong> ${m.advisory}</span>`;

  const tVal = weather.temperature !== null ? `${weather.temperature} ${weather.unit_temp}` : "--";
  const hVal = weather.humidity !== null ? `${weather.humidity} ${weather.unit_humidity}` : "--";
  const tempElem = document.getElementById("rtTemp");
  const humElem = document.getElementById("rtHumidity");
  if (tempElem) tempElem.textContent = tVal;
  if (humElem) humElem.textContent = hVal;

  updatePollutantCard("PM25", pols.pm25.value, 150, m.color);
  updatePollutantCard("PM10", pols.pm10.value, 250, m.color);
  updatePollutantCard("NO2", pols.no2.value, 120, m.color);
  updatePollutantCard("SO2", pols.so2.value, 100, m.color);
  updatePollutantCard("CO", pols.co.value, 10, m.color);
  updatePollutantCard("O3", pols.o3.value, 120, m.color);

  renderForecastChart(data.hourly_forecast);
  renderCityMap(data.latitude, data.longitude, data.city, m.aqi, m.category, m.color);
}

function updatePollutantCard(idKey, val, scaleMax, color) {
  const valElem = document.getElementById(`val${idKey}`);
  const fillElem = document.getElementById(`fill${idKey}`);

  if (valElem) {
    valElem.textContent = val !== null && val !== undefined ? val : "--";
  }

  if (fillElem && val !== null && val !== undefined) {
    const pct = Math.min(100, Math.max(5, (val / scaleMax) * 100));
    fillElem.style.width = `${pct}%`;
    fillElem.style.backgroundColor = color;
  }
}

function updateSidebarWidget(data) {
  const m = data.metrics;
  const sCity = document.getElementById("sidebarCityName");
  const sAqi = document.getElementById("sidebarAqiNum");
  const sBadge = document.getElementById("sidebarCategoryBadge");
  const sSub = document.getElementById("sidebarPollutantSub");

  if (sCity) sCity.textContent = data.city;
  if (sAqi) sAqi.textContent = m.aqi;
  if (sBadge) {
    sBadge.textContent = m.category;
    sBadge.style.backgroundColor = m.color;
    sBadge.style.color = "#ffffff";
  }
  if (sSub) sSub.textContent = `PM2.5: ${m.pollutants.pm25.value || "--"} | PM10: ${m.pollutants.pm10.value || "--"}`;
}

function renderForecastChart(forecast) {
  if (!forecast || !forecast.times || forecast.times.length === 0) return;

  const ctx = document.getElementById("hourlyForecastChart");
  if (!ctx) return;

  if (forecastChartInstance) {
    forecastChartInstance.destroy();
  }

  forecastChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: forecast.times,
      datasets: [
        {
          label: "PM2.5 (μg/m³)",
          data: forecast.pm25,
          borderColor: "#ef4444",
          backgroundColor: "rgba(239, 68, 68, 0.08)",
          borderWidth: 2.5,
          tension: 0.35,
          fill: true,
          pointRadius: 2.5
        },
        {
          label: "PM10 (μg/m³)",
          data: forecast.pm10,
          borderColor: "#0284c7",
          backgroundColor: "transparent",
          borderWidth: 2,
          borderDash: [4, 4],
          tension: 0.35,
          pointRadius: 2
        },
        {
          label: "AQI Index",
          data: forecast.aqi,
          borderColor: "#8b5cf6",
          backgroundColor: "transparent",
          borderWidth: 2,
          tension: 0.35,
          pointRadius: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(11, 25, 44, 0.95)",
          titleFont: { family: "Plus Jakarta Sans", size: 12 },
          bodyFont: { family: "Plus Jakarta Sans", size: 12 },
          padding: 10,
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "Plus Jakarta Sans", size: 11 }, maxTicksLimit: 12 }
        },
        y: {
          grid: { color: "#e2e8f0" },
          ticks: { font: { family: "Plus Jakarta Sans", size: 11 } }
        }
      }
    }
  });
}

function renderCityMap(lat, lon, cityName, aqi, category, color) {
  const mapContainer = document.getElementById("cityMap");
  if (!mapContainer) return;

  const mapTitle = document.getElementById("mapTitle");
  if (mapTitle) mapTitle.textContent = `${cityName} Station Coordinates`;

  if (!leafletMap) {
    leafletMap = L.map("cityMap", {
      center: [lat, lon],
      zoom: 11,
      zoomControl: true
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(leafletMap);
  } else {
    leafletMap.setView([lat, lon], 11);
  }

  if (mapMarker) leafletMap.removeLayer(mapMarker);
  if (mapCircle) leafletMap.removeLayer(mapCircle);

  mapCircle = L.circle([lat, lon], {
    color: color,
    fillColor: color,
    fillOpacity: 0.2,
    radius: 3500
  }).addTo(leafletMap);

  mapMarker = L.circleMarker([lat, lon], {
    radius: 9,
    fillColor: color,
    color: "#ffffff",
    weight: 3,
    opacity: 1,
    fillOpacity: 0.95
  }).addTo(leafletMap);

  mapMarker.bindPopup(`
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; text-align: center; padding: 4px;">
      <strong style="font-size: 14px; color: #0b192c;">${cityName}</strong><br/>
      <span style="display:inline-block; margin-top:4px; padding: 2px 8px; border-radius: 12px; background:${color}; color:#fff; font-weight:700; font-size:12px;">
        AQI: ${aqi} (${category})
      </span>
    </div>
  `).openPopup();
}


// =========================================================
// 5. PERSONA & PROFILE SELECTOR
// =========================================================
function togglePersonaMenu() {
  const menu = document.getElementById("personaMenu");
  if (menu) menu.classList.toggle("hidden");
}

function selectProfile(profileName) {
  AppState.currentPersona = profileName;

  const label = document.getElementById("activePersonaLabel");
  const chatLabel = document.getElementById("chatPersonaName");
  if (label) label.textContent = profileName;
  if (chatLabel) chatLabel.textContent = profileName;

  document.querySelectorAll(".p-menu-item").forEach(item => {
    item.classList.toggle("active", item.querySelector("strong").textContent === profileName);
  });

  const menu = document.getElementById("personaMenu");
  if (menu) menu.classList.add("hidden");
}


// =========================================================
// 6. PHASE 3: INTERACTIVE CHARTS & HISTORICAL FILTERS
// =========================================================
function initHistoricalViews() {
  renderComparePills();
  updateCityComparison();
  loadLeaderboard("PM2.5");
  loadTamilNaduTimeSeries();
  loadFilteredTimeSeries();
  loadNationalRankings();
}

async function loadFilteredTimeSeries() {
  const city = document.getElementById("histFilterCity") ? document.getElementById("histFilterCity").value : "All";
  const month = document.getElementById("histFilterMonth") ? document.getElementById("histFilterMonth").value : "All";
  const area = document.getElementById("histFilterArea") ? document.getElementById("histFilterArea").value : "All";

  const statusElem = document.getElementById("histFilterStatus");
  if (statusElem) statusElem.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Filtering authentic CPCB observations...`;

  try {
    const url = `/api/historical/time-series?city=${encodeURIComponent(city)}&month=${encodeURIComponent(month)}&area_type=${encodeURIComponent(area)}`;
    const resp = await fetch(url);
    const json = await resp.json();

    if (json.status === "success") {
      renderHistAqiTrendChart(json);
      if (statusElem) {
        statusElem.innerHTML = `<i class="fa-solid fa-circle-check text-green"></i> Loaded <strong>${json.total_records}</strong> authentic CPCB observations across ${city === "All" ? "all cities" : city}`;
      }
    } else {
      if (statusElem) {
        statusElem.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color:#d97706;"></i> ${json.message || "No records for selected criteria."}`;
      }
    }
  } catch (e) {
    console.error("Time-series fetch error:", e);
  }
}

function renderHistAqiTrendChart(data) {
  const ctx = document.getElementById("histAqiTrendChart");
  if (!ctx || !data.dates || data.dates.length === 0) return;

  if (histAqiTrendChartInstance) {
    histAqiTrendChartInstance.destroy();
  }

  histAqiTrendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.dates,
      datasets: [
        {
          label: "RSPM / PM10 (μg/m³)",
          data: data.pm10,
          borderColor: "#0284c7",
          backgroundColor: "rgba(2, 132, 199, 0.06)",
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.25,
          fill: true
        },
        {
          label: "PM2.5 (μg/m³)",
          data: data.pm25,
          borderColor: "#ef4444",
          backgroundColor: "transparent",
          borderWidth: 2.2,
          pointRadius: 2.5,
          tension: 0.25
        },
        {
          label: "NO2 (μg/m³)",
          data: data.no2,
          borderColor: "#f59e0b",
          backgroundColor: "transparent",
          borderWidth: 1.8,
          pointRadius: 1.5,
          tension: 0.25
        },
        {
          label: "SO2 (μg/m³)",
          data: data.so2,
          borderColor: "#10b981",
          backgroundColor: "transparent",
          borderWidth: 1.8,
          pointRadius: 1.5,
          tension: 0.25
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(11, 25, 44, 0.95)",
          padding: 10,
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "Plus Jakarta Sans", size: 10 }, maxTicksLimit: 14 }
        },
        y: {
          grid: { color: "#e2e8f0" },
          title: { display: true, text: "Concentration (μg/m³)" }
        }
      }
    }
  });
}

function applyHistoricalFilters() {
  loadFilteredTimeSeries();
}

function resetHistoricalFilters() {
  if (document.getElementById("histFilterCity")) document.getElementById("histFilterCity").value = "All";
  if (document.getElementById("histFilterMonth")) document.getElementById("histFilterMonth").value = "All";
  if (document.getElementById("histFilterArea")) document.getElementById("histFilterArea").value = "All";
  loadFilteredTimeSeries();
}

// 12-Month Longitudinal Trends (Tamil Nadu 2015)
async function loadTamilNaduTimeSeries() {
  try {
    const resp = await fetch("/api/historical/tamil-nadu-trends");
    const json = await resp.json();

    if (json.status === "success") {
      renderTamilNaduCharts(json);
    }
  } catch (e) {
    console.error("Failed to load Tamil Nadu trends:", e);
  }
}

function renderTamilNaduCharts(data) {
  const mTrend = data.monthly_trend;

  // 12-Month Line Chart
  const ctxMonthly = document.getElementById("monthlyTrendChart");
  if (ctxMonthly && mTrend) {
    if (monthlyTrendChartInstance) monthlyTrendChartInstance.destroy();

    monthlyTrendChartInstance = new Chart(ctxMonthly, {
      type: "line",
      data: {
        labels: mTrend.months,
        datasets: [
          {
            label: "RSPM / PM10 (μg/m³)",
            data: mTrend.pm10,
            borderColor: "#ef4444",
            backgroundColor: "rgba(239, 68, 68, 0.08)",
            borderWidth: 2.5,
            fill: true,
            tension: 0.35
          },
          {
            label: "NO2 (μg/m³)",
            data: mTrend.no2,
            borderColor: "#f59e0b",
            borderWidth: 2,
            tension: 0.35
          },
          {
            label: "SO2 (μg/m³)",
            data: mTrend.so2,
            borderColor: "#10b981",
            borderWidth: 2,
            tension: 0.35
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#e2e8f0" }, title: { display: true, text: "Monthly Mean (μg/m³)" } }
        }
      }
    });
  }

  // Seasonal
  const ctxSeasonal = document.getElementById("seasonalChart");
  if (ctxSeasonal && data.seasonal_comparison) {
    if (seasonalChartInstance) seasonalChartInstance.destroy();

    const sLabels = data.seasonal_comparison.map(s => s.season);
    const sPm10 = data.seasonal_comparison.map(s => s["RSPM/PM10"]);
    const sNo2 = data.seasonal_comparison.map(s => s["NO2"]);

    seasonalChartInstance = new Chart(ctxSeasonal, {
      type: "bar",
      data: {
        labels: sLabels,
        datasets: [
          { label: "RSPM/PM10", data: sPm10, backgroundColor: "#0284c7", borderRadius: 4 },
          { label: "NO2", data: sNo2, backgroundColor: "#f59e0b", borderRadius: 4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#e2e8f0" } }
        }
      }
    });
  }

  // Zoning
  const ctxZoning = document.getElementById("zoningChart");
  if (ctxZoning && data.location_type_comparison) {
    if (zoningChartInstance) zoningChartInstance.destroy();

    const zLabels = data.location_type_comparison.map(z => z["Type of Location"].replace("Area", ""));
    const zPm10 = data.location_type_comparison.map(z => z["RSPM/PM10"]);
    const zSo2 = data.location_type_comparison.map(z => z["SO2"]);

    zoningChartInstance = new Chart(ctxZoning, {
      type: "bar",
      data: {
        labels: zLabels,
        datasets: [
          { label: "RSPM/PM10", data: zPm10, backgroundColor: "#ef4444", borderRadius: 4 },
          { label: "SO2", data: zSo2, backgroundColor: "#10b981", borderRadius: 4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#e2e8f0" } }
        }
      }
    });
  }
}

// Multi-City Comparison
function renderComparePills() {
  const container = document.getElementById("compareCityPills");
  if (!container) return;

  container.innerHTML = AppState.compareCities.map(c => `
    <span class="compare-pill">
      ${c}
      <i class="fa-solid fa-xmark remove-pill" onclick="removeCompareCity('${c}')"></i>
    </span>
  `).join("");
}

function removeCompareCity(cityName) {
  if (AppState.compareCities.length <= 2) {
    alert("Please keep at least 2 cities for side-by-side comparison.");
    return;
  }
  AppState.compareCities = AppState.compareCities.filter(c => c.toLowerCase() !== cityName.toLowerCase());
  renderComparePills();
  updateCityComparison();
}

function setComparePreset(cityArray) {
  AppState.compareCities = [...cityArray];
  renderComparePills();
  updateCityComparison();
}

async function updateCityComparison() {
  try {
    const resp = await fetch("/api/historical/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cities: AppState.compareCities })
    });
    const json = await resp.json();

    if (json.status === "success" && json.comparison) {
      renderComparisonCharts(json.comparison);
    }
  } catch (e) {
    console.error("Failed to fetch city comparison:", e);
  }
}

function renderComparisonCharts(comp) {
  const cities = comp.cities || [];
  const matrix = comp.matrix || {};

  const pm25Data = cities.map(c => (matrix[c] ? matrix[c]["PM2.5"] || 0 : 0));
  const pm10Data = cities.map(c => (matrix[c] ? matrix[c]["PM10"] || 0 : 0));

  const ctxPart = document.getElementById("compareParticulateChart");
  if (ctxPart) {
    if (compareParticulateChartInstance) compareParticulateChartInstance.destroy();

    compareParticulateChartInstance = new Chart(ctxPart, {
      type: "bar",
      data: {
        labels: cities,
        datasets: [
          { label: "PM2.5 (Fine Particulates)", data: pm25Data, backgroundColor: "#ef4444", borderRadius: 6 },
          { label: "PM10 (Coarse Dust)", data: pm10Data, backgroundColor: "#0284c7", borderRadius: 6 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#e2e8f0" }, title: { display: true, text: "Concentration (μg/m³)" } }
        }
      }
    });
  }

  const no2Data = cities.map(c => (matrix[c] ? matrix[c]["NO2"] || 0 : 0));
  const so2Data = cities.map(c => (matrix[c] ? matrix[c]["SO2"] || 0 : 0));
  const coData = cities.map(c => (matrix[c] ? matrix[c]["CO"] || 0 : 0));
  const o3Data = cities.map(c => (matrix[c] ? matrix[c]["OZONE"] || 0 : 0));

  const ctxGas = document.getElementById("compareGasesChart");
  if (ctxGas) {
    if (compareGasesChartInstance) compareGasesChartInstance.destroy();

    compareGasesChartInstance = new Chart(ctxGas, {
      type: "bar",
      data: {
        labels: cities,
        datasets: [
          { label: "NO2", data: no2Data, backgroundColor: "#f59e0b", borderRadius: 4 },
          { label: "SO2", data: so2Data, backgroundColor: "#10b981", borderRadius: 4 },
          { label: "CO", data: coData, backgroundColor: "#6366f1", borderRadius: 4 },
          { label: "OZONE", data: o3Data, backgroundColor: "#ec4899", borderRadius: 4 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: "#e2e8f0" } }
        }
      }
    });
  }
}


// =========================================================
// 7. PHASE 4: LEADERBOARDS & ADVANCED ANALYTICS
// =========================================================
function setLeaderboardMode(mode) {
  AppState.leaderboardMode = mode;
  document.getElementById("btnModePolluted").classList.toggle("active", mode === "polluted");
  document.getElementById("btnModeCleanest").classList.toggle("active", mode === "cleanest");

  loadLeaderboard(AppState.currentLeaderboardPollutant);
}

function changeLeaderboardPollutant(pollutant) {
  AppState.currentLeaderboardPollutant = pollutant;
  loadLeaderboard(pollutant);
}

async function loadLeaderboard(pollutant) {
  document.querySelectorAll(".toggle-pill-group .toggle-pill").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.pol === pollutant);
  });

  const isClean = AppState.leaderboardMode === "cleanest";
  const titleElem = document.getElementById("lbChartTitle");
  const headerElem = document.getElementById("ranksListHeader");

  if (titleElem) {
    titleElem.textContent = isClean
      ? `Top 10 Cleanest Cities by Lowest ${pollutant} Concentration (CPCB Dataset)`
      : `Top 10 Most Polluted Cities by Average ${pollutant} Concentration (CPCB Dataset)`;
  }
  if (headerElem) {
    headerElem.textContent = isClean ? "Cleanest Cities (Valid Data)" : "Most Polluted Cities";
  }

  const endpoint = isClean
    ? `/api/historical/cleanest?pollutant=${pollutant}&limit=10`
    : `/api/historical/top?pollutant=${pollutant}&limit=10`;

  try {
    const resp = await fetch(endpoint);
    const json = await resp.json();

    if (json.status === "success" && Array.isArray(json.data)) {
      renderLeaderboardView(json.data, pollutant, isClean);
    }
  } catch (e) {
    console.error("Failed to load leaderboard:", e);
  }
}

function renderLeaderboardView(data, pollutant, isClean = false) {
  const listContainer = document.getElementById("leaderboardList");
  if (listContainer) {
    listContainer.innerHTML = data.map(item => `
      <div class="rank-item" onclick="selectCityByName('${item.city}')">
        <div class="rank-badge ${isClean ? 'rank-clean' : 'rank-' + item.rank}">#${item.rank}</div>
        <div class="rank-city-info">
          <strong>${item.city}</strong>
          <span>${item.state} &bull; ${item.stations} station(s)</span>
        </div>
        <div class="rank-val">
          <strong>${item.value}</strong>
          <span class="muted-unit">${pollutant === "CO" ? "mg/m³" : "μg/m³"}</span>
        </div>
      </div>
    `).join("");
  }

  const ctx = document.getElementById("leaderboardChart");
  if (!ctx) return;

  if (leaderboardChartInstance) leaderboardChartInstance.destroy();

  const labels = data.map(d => d.city).reverse();
  const values = data.map(d => d.value).reverse();
  const chartColor = isClean ? "#10b981" : (pollutant === "PM2.5" ? "#ef4444" : pollutant === "PM10" ? "#f97316" : "#0284c7");

  leaderboardChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: isClean ? `Lowest ${pollutant}` : `Average ${pollutant}`,
        data: values,
        backgroundColor: chartColor,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { cornerRadius: 8 }
      },
      scales: {
        x: { grid: { color: "#e2e8f0" } },
        y: { grid: { display: false } }
      }
    }
  });
}

// National Rankings Table
async function loadNationalRankings() {
  try {
    const resp = await fetch("/api/historical/rankings?pollutant=PM2.5");
    const json = await resp.json();
    if (json.status === "success" && Array.isArray(json.rankings)) {
      AppState.rankingsData = json.rankings;
      AppState.filteredRankings = json.rankings;
      renderNationalRankingsTable();
    }
  } catch (e) {
    console.error("National rankings fetch error:", e);
  }
}

function filterRankingTable() {
  const query = (document.getElementById("rankingTableSearch") ? document.getElementById("rankingTableSearch").value : "").trim().toLowerCase();
  if (!query) {
    AppState.filteredRankings = AppState.rankingsData;
  } else {
    AppState.filteredRankings = AppState.rankingsData.filter(r =>
      r.city.toLowerCase().includes(query) || (r.state && r.state.toLowerCase().includes(query))
    );
  }
  AppState.rankPage = 1;
  renderNationalRankingsTable();
}

function renderNationalRankingsTable() {
  const tbody = document.getElementById("allCitiesRankBody");
  if (!tbody) return;

  const total = AppState.filteredRankings.length;
  AppState.rankTotalPages = Math.max(1, Math.ceil(total / AppState.rankPageSize));
  const start = (AppState.rankPage - 1) * AppState.rankPageSize;
  const pageSlice = AppState.filteredRankings.slice(start, start + AppState.rankPageSize);

  if (pageSlice.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="padding:20px;">No matching cities found.</td></tr>`;
  } else {
    tbody.innerHTML = pageSlice.map(r => {
      let badgeClass = "badge-good";
      if (r.category === "Satisfactory") badgeClass = "badge-satisfactory";
      else if (r.category === "Moderate") badgeClass = "badge-moderate";
      else if (r.category === "Poor") badgeClass = "badge-poor";
      else if (r.category === "Very Poor") badgeClass = "badge-very-poor";
      else if (r.category === "Severe") badgeClass = "badge-severe";

      return `
        <tr onclick="selectCityByName('${r.city}')" style="cursor:pointer;">
          <td><strong>#${r.rank}</strong></td>
          <td><strong>${r.city}</strong></td>
          <td>${r.state}</td>
          <td><strong>${r.value} μg/m³</strong></td>
          <td><span class="category-pill ${badgeClass}" style="font-size:0.75rem; padding:2px 8px;">${r.category}</span></td>
          <td>${r.percentile}%</td>
          <td>${r.stations}</td>
        </tr>
      `;
    }).join("");
  }

  const pInfo = document.getElementById("rankPaginationInfo");
  if (pInfo) {
    pInfo.textContent = `Showing ${Math.min(start + 1, total)} to ${Math.min(start + AppState.rankPageSize, total)} of ${total} cities`;
  }

  const pCounter = document.getElementById("rankPageCounter");
  if (pCounter) pCounter.textContent = `Page ${AppState.rankPage} of ${AppState.rankTotalPages}`;

  const prevBtn = document.getElementById("btnPrevRankPage");
  const nextBtn = document.getElementById("btnNextRankPage");
  if (prevBtn) prevBtn.disabled = (AppState.rankPage <= 1);
  if (nextBtn) nextBtn.disabled = (AppState.rankPage >= AppState.rankTotalPages);
}

function changeRankPage(delta) {
  const newPage = AppState.rankPage + delta;
  if (newPage >= 1 && newPage <= AppState.rankTotalPages) {
    AppState.rankPage = newPage;
    renderNationalRankingsTable();
  }
}

// Phase 4: Advanced Statistical Summary
async function loadAdvancedAnalytics() {
  const tbody = document.getElementById("statSummaryBody");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="9" class="text-center" style="padding:20px;">Computing descriptive statistics from 3,737 CPCB station records...</td></tr>`;

  try {
    const resp = await fetch("/api/historical/statistics");
    const json = await resp.json();

    if (json.status === "success" && json.statistics) {
      const stats = json.statistics;
      const order = ["PM2.5", "PM10", "NO2", "SO2", "CO", "OZONE", "NH3"];
      const limits = {
        "PM2.5": "60 μg/m³",
        "PM10": "100 μg/m³",
        "NO2": "80 μg/m³",
        "SO2": "80 μg/m³",
        "CO": "2.0 mg/m³",
        "OZONE": "100 μg/m³",
        "NH3": "400 μg/m³"
      };

      tbody.innerHTML = order.map(pid => {
        const s = stats[pid];
        if (!s) return "";
        return `
          <tr>
            <td><strong>${pid}</strong></td>
            <td>${s.count.toLocaleString()}</td>
            <td><strong>${s.mean}</strong></td>
            <td>${s.median}</td>
            <td>${s.std}</td>
            <td>${s.min}</td>
            <td>${s.max}</td>
            <td><strong style="color:${s.p90 > parseFloat(limits[pid]) ? '#ef4444' : '#10b981'};">${s.p90}</strong></td>
            <td><span class="badge" style="background:#e0f2fe; color:#0369a1;">${limits[pid]}</span></td>
          </tr>
        `;
      }).join("");
    }
  } catch (e) {
    console.error("Advanced analytics fetch error:", e);
  }
}

// Download Historical Reports
function downloadCsvReport(reportType) {
  window.location.href = `/api/historical/export?report_type=${encodeURIComponent(reportType)}`;
}


// =========================================================
// 8. MACHINE LEARNING PM10 PREDICTOR
// =========================================================
async function handleMlPredict(event) {
  event.preventDefault();

  const city = document.getElementById("mlCity").value;
  const stnCode = parseInt(document.getElementById("mlStnCode").value) || 768;
  const so2 = parseFloat(document.getElementById("mlSo2").value) || 12.0;
  const no2 = parseFloat(document.getElementById("mlNo2").value) || 25.0;
  const month = parseInt(document.getElementById("mlMonth").value) || 11;
  const dayOfYear = parseInt(document.getElementById("mlDayOfYear").value) || 315;

  const btn = document.getElementById("btnPredictPm10");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running Random Forest...`;
  }

  try {
    const resp = await fetch("/api/ml/predict-pm10", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        City: city,
        StnCode: stnCode,
        SO2: so2,
        NO2: no2,
        Month: month,
        DayOfYear: dayOfYear
      })
    });

    const data = await resp.json();
    if (data.status === "success") {
      const predVal = data.predicted_pm10;
      document.getElementById("mlPredictedVal").textContent = predVal;

      const tag = document.getElementById("mlCategoryTag");
      const interp = document.getElementById("mlInterpretation");

      if (predVal <= 50) {
        tag.textContent = "Good / Minimal Hazard";
        tag.style.backgroundColor = "#dcfce7";
        tag.style.color = "#166534";
      } else if (predVal <= 100) {
        tag.textContent = "Satisfactory";
        tag.style.backgroundColor = "#ecfccb";
        tag.style.color = "#3f6212";
      } else if (predVal <= 250) {
        tag.textContent = "Moderate Concern";
        tag.style.backgroundColor = "#fef9c3";
        tag.style.color = "#854d0e";
      } else {
        tag.textContent = "Elevated Respirable Dust Hazard";
        tag.style.backgroundColor = "#fee2e2";
        tag.style.color = "#991b1b";
      }

      interp.textContent = `Random Forest Regressor predicts a concentration of ${predVal} μg/m³ PM10 for ${city} during Month ${month} with SO2 at ${so2} μg/m³ and NO2 at ${no2} μg/m³.`;
    }
  } catch (err) {
    console.error("ML Prediction Error:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-microchip"></i> Run Model Inference`;
    }
  }
}


// =========================================================
// 9. AI HEALTH ADVISOR & RAG CHATBOT
// =========================================================
function updateChatbotContext(data) {
  if (!data || !data.metrics) return;
  const m = data.metrics;

  const ctxCity = document.getElementById("chatContextCity");
  const ctxAqi = document.getElementById("chatContextAqi");
  const ctxBadge = document.getElementById("chatContextBadge");
  const ctxPol = document.getElementById("chatContextPollutants");

  if (ctxCity) ctxCity.textContent = data.city;
  if (ctxAqi) ctxAqi.textContent = m.aqi;
  if (ctxBadge) {
    ctxBadge.textContent = m.category;
    ctxBadge.style.backgroundColor = m.color;
    ctxBadge.style.color = "#ffffff";
  }
  if (ctxPol) {
    ctxPol.textContent = `PM2.5: ${m.pollutants.pm25.value || "--"} μg/m³ | PM10: ${m.pollutants.pm10.value || "--"} μg/m³`;
  }
}

function addChatMessage(message, sender) {
  const chatStream = document.getElementById("chatStream");
  if (!chatStream) return;

  const bubble = document.createElement("div");
  bubble.className = sender === "user" ? "chat-bubble user-bubble" : "chat-bubble bot-bubble";

  const header = document.createElement("div");
  header.className = "bubble-header";
  header.innerHTML = sender === "user"
    ? `<i class="fa-solid fa-user"></i> You (${AppState.currentPersona})`
    : `<i class="fa-solid fa-robot"></i> AirAssist AI (${AppState.currentCity})`;

  const body = document.createElement("div");
  body.className = "bubble-body";

  if (typeof message === "object" && message !== null) {
    if (message.is_emergency) {
      body.innerHTML = `
        <div style="background:#fee2e2; border:1px solid #fecaca; border-radius:8px; padding:12px; color:#991b1b;">
          <strong><i class="fa-solid fa-triangle-exclamation"></i> ${message.emergency_title}</strong>
          <p style="margin:6px 0;">${message.emergency_message}</p>
          <div style="font-weight:700;"><i class="fa-solid fa-phone"></i> ${message.emergency_action}</div>
        </div>
      `;
    } else {
      let html = "";
      if (message.custom_answer) {
        html += `<p style="margin-bottom:8px;">${message.custom_answer}</p>`;
      }
      if (message.recommendations && message.recommendations.length > 0) {
        html += `<strong>Protective Action Plan:</strong><ul style="margin:6px 0 10px 18px;">`;
        message.recommendations.forEach(r => { html += `<li>${r}</li>`; });
        html += `</ul>`;
      }
      if (message.mask_advice) {
        html += `<div style="margin:4px 0;"><i class="fa-solid fa-head-side-mask"></i> <strong>Mask Advice:</strong> ${message.mask_advice}</div>`;
      }
      if (message.indoor_advice) {
        html += `<div style="margin:4px 0;"><i class="fa-solid fa-fan"></i> <strong>Indoor Air:</strong> ${message.indoor_advice}</div>`;
      }
      body.innerHTML = html;
    }
  } else {
    body.innerHTML = message.replace(/\n/g, "<br/>");
  }

  bubble.appendChild(header);
  bubble.appendChild(body);
  chatStream.appendChild(bubble);
  chatStream.scrollTop = chatStream.scrollHeight;
}

function showTypingMessage() {
  const chatStream = document.getElementById("chatStream");
  const typingBubble = document.createElement("div");
  typingBubble.className = "chat-bubble bot-bubble";
  typingBubble.id = "chatTyping";

  typingBubble.innerHTML = `
    <div class="bubble-header"><i class="fa-solid fa-robot"></i> AirAssist AI</div>
    <div class="bubble-body"><i class="fa-solid fa-spinner fa-spin"></i> Retrieving live AQI and clinical guidelines...</div>
  `;

  chatStream.appendChild(typingBubble);
  chatStream.scrollTop = chatStream.scrollHeight;
  return typingBubble;
}

async function handleChatSubmit(event) {
  if (event) event.preventDefault();

  const input = document.getElementById("chatInput");
  if (!input) return;

  const question = input.value.trim();
  if (!question) return;

  input.value = "";
  await sendChatQuery(question);
}

function sendQuickQuery(queryText) {
  switchNavTab("chatbot");
  sendChatQuery(queryText);
}

async function sendChatQuery(question) {
  if (AppState.isChatLoading) return;
  AppState.isChatLoading = true;

  const sendBtn = document.getElementById("btnSendChat");
  if (sendBtn) {
    sendBtn.disabled = true;
    sendBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
  }

  addChatMessage(question, "user");
  const typingBubble = showTypingMessage();

  try {
    // Attempt Gemini RAG Chatbot endpoint
    let response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question })
    });

    if (response.ok) {
      const data = await response.json();
      if (typingBubble) typingBubble.remove();

      if (data.status === "success" && data.answer) {
        addChatMessage(data.answer, "bot");
        return;
      }
    }

    // Fallback: Deterministic Clinical RAG Advisory engine
    const advResp = await fetch("/api/ai-advisor/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city: AppState.currentCity,
        persona: AppState.currentPersona,
        query: question,
        lat: AppState.currentLat,
        lon: AppState.currentLon
      })
    });

    if (typingBubble) typingBubble.remove();
    const advData = await advResp.json();

    if (advData.status === "success" && advData.advisory) {
      addChatMessage(advData.advisory, "bot");
    } else {
      addChatMessage("Unable to process advisory at this moment. Please refer to our Health Guide tab.", "bot");
    }
  } catch (err) {
    if (typingBubble) typingBubble.remove();
    addChatMessage("Error reaching advisory service. Please check that the Flask server is running.", "bot");
  } finally {
    AppState.isChatLoading = false;
    if (sendBtn) {
      sendBtn.disabled = false;
      sendBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send`;
    }
  }
}


// =========================================================
// 10. EXPOSE FUNCTIONS TO WINDOW FOR HTML EVENT HANDLERS
// =========================================================
window.switchNavTab = switchNavTab;
window.toggleSidebar = toggleSidebar;
window.togglePersonaMenu = togglePersonaMenu;
window.selectProfile = selectProfile;
window.selectCityByName = selectCityByName;
window.refreshRealtimeData = refreshRealtimeData;
window.applyHistoricalFilters = applyHistoricalFilters;
window.resetHistoricalFilters = resetHistoricalFilters;
window.setLeaderboardMode = setLeaderboardMode;
window.changeLeaderboardPollutant = changeLeaderboardPollutant;
window.filterRankingTable = filterRankingTable;
window.changeRankPage = changeRankPage;
window.downloadCsvReport = downloadCsvReport;
window.removeCompareCity = removeCompareCity;
window.setComparePreset = setComparePreset;
window.handleMlPredict = handleMlPredict;
window.handleChatSubmit = handleChatSubmit;
window.sendQuickQuery = sendQuickQuery;
