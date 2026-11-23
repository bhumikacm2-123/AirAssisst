"""
AirAssist - AI Health Advisory & RAG Engine
Combines real-time air quality metrics with clinical evidence from:
- WHO Global Air Quality Guidelines (2021)
- ICMR (Indian Council of Medical Research) Advisories
- AIIMS Delhi Respiratory Protocols & Mask Standards (BIS 9473 / N95)
"""

import re
from typing import Dict, Any, List, Optional

# Knowledge Base Chunks for Clinical Grounding
CLINICAL_KNOWLEDGE = {
    "who_thresholds": {
        "PM2.5": "WHO 24-hour guideline is 15 μg/m³; annual guideline is 5 μg/m³.",
        "PM10": "WHO 24-hour guideline is 45 μg/m³; annual guideline is 15 μg/m³.",
        "NO2": "WHO 24-hour guideline is 25 μg/m³.",
        "O3": "WHO 8-hour seasonal guideline is 100 μg/m³.",
        "SO2": "WHO 24-hour guideline is 40 μg/m³.",
        "CO": "WHO 24-hour guideline is 4 mg/m³.",
    },
    "masks": {
        "N95_FFP2": "Certified N95, FFP2, or BIS 9473 masks filter ≥95% of airborne particles down to 0.3 microns. Ensure an airtight nasal pinch seal.",
        "surgical_cloth": "Surgical and cloth masks block large droplets but provide minimal seal against PM2.5 particles, which penetrate deep into alveoli and bloodstream.",
    },
    "indoor_purification": {
        "hepa": "True HEPA (H13 grade) mechanically captures 99.97% of PM2.5. Select an air purifier with a CADR (Clean Air Delivery Rate) suitable for your room area.",
        "ionizer_warning": "Avoid purifiers with uncertified ionizers or ozone generators, as secondary ozone irritates airway epithelial cells.",
    },
    "exercise": {
        "aerobic_risk": "During vigorous aerobic exercise (running, cycling), minute ventilation increases 5-10x, dramatically multiplying particulate deposition into lung tissue.",
        "inversion_warning": "In winter months, thermal inversion traps particulate pollution near the surface between 5:00 AM and 9:00 AM. Shift aerobic activities indoors or to late afternoons.",
    },
}

# Red-flag medical emergency symptoms requiring immediate hospitalization
EMERGENCY_KEYWORDS = [
    "chest pain", "cannot breathe", "can't breathe", "struggling to breathe",
    "blue lips", "bluish skin", "cyanosis", "unconscious", "fainted",
    "gasping", "oxygen below 90", "spO2 88", "spO2 85", "severe attack"
]


def check_emergency_indicators(query: str) -> bool:
    """Detects acute clinical distress requiring immediate emergency escalation."""
    q_lower = query.lower()
    return any(k in q_lower for k in EMERGENCY_KEYWORDS)


def generate_personalized_health_advisory(
    user_persona: str,
    city: str,
    aqi: float,
    pollutants: Dict[str, Any],
    user_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    RAG-grounded advisory generator combining:
    1. Real-time AQI and pollutant concentrations
    2. Specific demographic vulnerability profile
    3. User question intent
    4. Guardrails and medical disclaimers
    """
    aqi_val = round(aqi) if aqi is not None else 120
    pm25_val = pollutants.get("pm25", {}).get("value", 0) or 0
    pm10_val = pollutants.get("pm10", {}).get("value", 0) or 0
    no2_val = pollutants.get("no2", {}).get("value", 0) or 0
    co_val = pollutants.get("co", {}).get("value", 0) or 0

    # 1. Emergency Safety Check
    if user_query and check_emergency_indicators(user_query):
        return {
            "is_emergency": True,
            "emergency_title": "URGENT MEDICAL ALERT",
            "emergency_message": (
                "The symptoms you described (such as severe breathing distress or chest pain) "
                "require IMMEDIATE medical attention. Please do not wait."
            ),
            "emergency_action": "Call National Emergency Ambulance: 108 or 112 immediately. Keep the patient upright in a well-ventilated, filtered room.",
            "disclaimer": "AirAssist is an informational platform and does not replace emergency clinical triage."
        }

    # 2. Risk Tier Classification
    if aqi_val <= 50:
        tier = "Good"
        risk_level = "Minimal"
        color = "#10b981"
    elif aqi_val <= 100:
        tier = "Satisfactory"
        risk_level = "Low"
        color = "#84cc16"
    elif aqi_val <= 200:
        tier = "Moderate"
        risk_level = "Medium"
        color = "#eab308"
    elif aqi_val <= 300:
        tier = "Poor"
        risk_level = "High"
        color = "#f97316"
    elif aqi_val <= 400:
        tier = "Very Poor"
        risk_level = "Very High"
        color = "#ef4444"
    else:
        tier = "Severe"
        risk_level = "Hazardous"
        color = "#7c2d12"

    # 3. Persona Specific Tailoring
    persona_key = (user_persona or "general").lower()
    recommendations = []
    persona_notice = ""
    mask_advice = ""
    indoor_advice = ""
    activity_advice = ""

    if "asthma" in persona_key or "copd" in persona_key or "respiratory" in persona_key:
        persona_notice = "High Respiratory Sensitivity: Airway hyper-reactivity triggered by PM2.5 and nitrogen dioxide."
        if aqi_val > 150:
            recommendations.append("Keep your prescribed rescue inhaler (e.g., Salbutamol/Levosalbutamol) on hand at all times.")
            recommendations.append("Avoid stepping outdoors during morning inversion peaks (6:00 AM - 9:30 AM).")
            recommendations.append("Do not modify maintenance doses without consulting your pulmonologist.")
        else:
            recommendations.append("Safe for light outdoor activity, but monitor for bronchospasm or throat tickling.")
        
        mask_advice = "Wear a fitted N95 mask if exposed to outdoor air for more than 15 minutes."
        indoor_advice = "Run a True HEPA air purifier continuously in the bedroom with doors and windows closed."
        activity_advice = "Replace outdoor walks with indoor stretching or treadmill sessions."

    elif "senior" in persona_key or "elderly" in persona_key:
        persona_notice = "Cardiopulmonary Vulnerability: Fine particulates increase blood viscosity and systemic inflammation."
        if aqi_val > 150:
            recommendations.append("Postpone early morning walks to afternoon hours (2:00 PM - 5:00 PM) when the boundary layer rises.")
            recommendations.append("Stay well hydrated to maintain mucosal barrier defense in upper respiratory passages.")
            recommendations.append("Monitor blood pressure and pulse; seek medical review if breathlessness occurs.")
        else:
            recommendations.append("Favorable conditions for morning park walks; maintain comfortable pacing.")
        
        mask_advice = "N95 / FFP2 mask recommended during vehicular commute."
        indoor_advice = "Keep indoor areas dust-free; use damp mopping rather than dry sweeping to prevent particle re-suspension."
        activity_advice = "Gentle yoga and indoor walking are strongly advised during elevated AQI hours."

    elif "child" in persona_key or "school" in persona_key or "parent" in persona_key:
        persona_notice = "Pediatric Physiology: Children breathe 50% more air per kilogram of body weight than adults, increasing dose per lung area."
        if aqi_val > 200:
            recommendations.append("School authorities should cancel outdoor sports and physical training periods.")
            recommendations.append("Children should not wait outdoors at bus stops for prolonged periods without protection.")
            recommendations.append("Watch for dry coughing, eye redness, or wheezing.")
        else:
            recommendations.append("Normal outdoor play is permissible, with adequate hydration.")
        
        mask_advice = "If stepping out in high AQI, use child-sized certified masks (adult N95s leave critical side air leaks)."
        indoor_advice = "Keep classrooms and bedrooms sealed with HEPA filtration if AQI > 250."
        activity_advice = "Switch physical education to indoor gymnastics, chess, or table tennis."

    elif "outdoor" in persona_key or "worker" in persona_key or "rider" in persona_key or "delivery" in persona_key:
        persona_notice = "High Occupational Exposure: Prolonged 8-10 hour exposure to vehicular exhaust, diesel particulates, and road dust."
        recommendations.append("Wear an N95/FFP2 mask with a tight nose clip throughout your transit shift. Cloth masks do not filter PM2.5.")
        recommendations.append("Rinse eyes with sterile saline or clean water after shifts to remove irritant particles.")
        recommendations.append("Take resting breaks inside air-conditioned shops or hubs with filtered air.")
        recommendations.append("Wear protective wrap-around goggles if riding a two-wheeler in high dust zones.")
        
        mask_advice = "Mandatory N95 / BIS 9473 respirator. Replace after 24-40 hours of cumulative use or if breathing resistance rises."
        indoor_advice = "Sleep in a closed room with air purification to allow respiratory cilia recovery overnight."
        activity_advice = "Avoid tailgating diesel trucks or standing in idling intersections during congestion."

    elif "runner" in persona_key or "fitness" in persona_key or "athlete" in persona_key:
        persona_notice = "High Ventilation Rate: Athletes inhale up to 100 liters of air per minute during tempo workouts, depositing deep micro-pollutants."
        if aqi_val > 150:
            recommendations.append("Cancel high-intensity interval training (HIIT) and tempo runs outdoors.")
            recommendations.append("Shift your training session to an indoor gym with active air conditioning and filtration.")
            recommendations.append("Never run along major arterial roads or ring roads where NO2 and black carbon peak.")
        else:
            recommendations.append("Acceptable for outdoor runs. Prefer green parks with dense tree canopies over roadside tracks.")
        
        mask_advice = "Do not sprint with an N95 mask due to high breathing resistance; instead, move your workout indoors."
        indoor_advice = "Maintain high-efficiency filters in your home training space."
        activity_advice = "Schedule workouts between 12:00 PM and 4:00 PM when solar heat lifts ground-level pollutant smog."

    else:  # General Adult
        persona_notice = "General Public Guidance: Maintain standard environmental vigilance."
        if aqi_val > 200:
            recommendations.append("Limit unnecessary outdoor stays and avoid heavy manual exertion outdoors.")
            recommendations.append("Keep windows closed in homes and offices during peak traffic hours.")
            recommendations.append("Stay hydrated and consume antioxidant-rich foods (vitamin C and E).")
        else:
            recommendations.append("Air quality is manageable; normal daily activities can proceed.")
        
        mask_advice = "Use an N95 respirator if traveling in open auto-rickshaws or walking beside high-traffic avenues."
        indoor_advice = "Ventilate your home in the afternoon when outdoor AQI is at its daytime minimum."
        activity_advice = "Normal daily routine with sensible precautions."

    # 4. Synthesize Question-Specific Answer if query provided
    custom_answer = None
    if user_query:
        q_lower = user_query.lower()
        if "run" in q_lower or "jog" in q_lower or "exercise" in q_lower or "walk" in q_lower:
            if aqi_val > 200:
                custom_answer = (
                    f"In {city} today (AQI {aqi_val} - {tier}), outdoor running or vigorous jogging is NOT recommended. "
                    f"At this concentration ({pm25_val} μg/m³ PM2.5), deep pulmonary inhalation can cause airway inflammation "
                    "and acute bronchoconstriction. Please exercise indoors or on a gym treadmill."
                )
            elif aqi_val > 100:
                custom_answer = (
                    f"Light walking is acceptable in {city} (AQI {aqi_val}), but intense cardiovascular running should be shifted "
                    "to an indoor space or delayed until the afternoon when thermal inversion clears."
                )
            else:
                custom_answer = f"The air quality in {city} (AQI {aqi_val} - {tier}) is favorable for outdoor running and exercise."

        elif "mask" in q_lower:
            custom_answer = (
                f"For the current air quality in {city} (PM2.5: {pm25_val} μg/m³), you should wear an N95 or FFP2 certified mask. "
                "Standard surgical masks and cloth scarves leak air around the nose and cheeks and do NOT filter sub-micron particles."
            )
        elif "purifier" in q_lower or "filter" in q_lower:
            custom_answer = (
                f"With {city}'s current AQI at {aqi_val}, a True HEPA (H13 grade) air purifier is "
                + ("STRONGLY RECOMMENDED" if aqi_val > 150 else "BENEFICIAL")
                + " for bedrooms and living spaces. Ensure the Clean Air Delivery Rate (CADR) matches your room size, and avoid ionizers."
            )
        elif "school" in q_lower or "child" in q_lower:
            if aqi_val > 250:
                custom_answer = (
                    f"Given {city}'s severe pollution level (AQI {aqi_val}), schools should strictly suspend all outdoor assemblies, "
                    "sports practices, and recess activities. Children should remain inside closed classrooms with filtration."
                )
            else:
                custom_answer = f"Children in {city} can attend school, but outdoor exposure should be moderated if AQI approaches 200."
        else:
            custom_answer = (
                f"Based on real-time data for {city} (AQI {aqi_val}, PM2.5: {pm25_val} μg/m³, PM10: {pm10_val} μg/m³), "
                f"the environmental health risk is categorized as '{risk_level}'. {persona_notice}"
            )

    return {
        "is_emergency": False,
        "city": city,
        "aqi": aqi_val,
        "tier": tier,
        "risk_level": risk_level,
        "color": color,
        "persona": user_persona,
        "persona_notice": persona_notice,
        "recommendations": recommendations,
        "mask_advice": mask_advice,
        "indoor_advice": indoor_advice,
        "activity_advice": activity_advice,
        "custom_answer": custom_answer,
        "pollutant_summary": f"PM2.5: {pm25_val} μg/m³ | PM10: {pm10_val} μg/m³ | NO2: {no2_val} μg/m³ | CO: {co_val} mg/m³",
        "clinical_citations": [
            "World Health Organization (WHO) Global Air Quality Guidelines (2021)",
            "Indian Council of Medical Research (ICMR) Environmental Health Guidance",
            "Bureau of Indian Standards (BIS 9473) Respiratory Protective Devices"
        ],
        "disclaimer": "AirAssist provides preventive public health advice grounded in environmental guidelines. It is not a clinical prescription."
    }
