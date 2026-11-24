"""
AutoAssist AI - Multilingual Query Normalization Bridge
Supports 7 Languages: English (en), Kannada (kn), Hindi (hi), Urdu (ur), Malayalam (ml), Tamil (ta), Telugu (te)
Normalizes non-English vernacular automotive symptom descriptions to English technical concepts
before executing 384-dimensional dense vector embeddings against OEM factory service manuals.
"""
import re
from typing import Dict, List, Tuple

# Multilingual automotive keyword map across the 7 supported languages
MULTILINGUAL_AUTOMOTIVE_MAP: List[Tuple[List[str], str]] = [
    # Overheating & Cooling
    (
        [
            "ಬಿಸಿ", "ಹೀಟ್", "ಕುದಿಯುತ್ತಿದೆ", "ರೇಡಿಯೇಟರ್", "ಕೂಲೆಂಟ್", "ಎಂಜಿನ್ ಬಿಸಿ",
            "गरम", "तापमान", "गर्म", "रेडिएटर", "कूलेंट", "उबल", "इंजन गरम",
            "گرم", "حرارت", "انجن گرم", "ریڈی ایٹر", "کولنٹ",
            "ചൂട്", "റേഡിയേറ്റർ", "കൂളന്റ്", "ചൂടാകുന്നു", "എഞ്ചിൻ ചൂട്",
            "வெப்பம்", "சூடு", "ரேடியேட்டர்", "கூலன்ட்", "என்ஜின் சூடு",
            "వేడి", "వేడెక్కుతోంది", "రేడియేటర్", "కూలెంట్", "ఇంజన్ వేడి",
            "overheat", "overheating", "hot engine", "boiling", "coolant", "radiator", "thermostat"
        ],
        "engine overheating coolant loss radiator temperature high"
    ),
    # Brakes & Stopping
    (
        [
            "ಬ್ರೇಕ್", "ನಿಲ್ತಿಲ್ಲ", "ಸದ್ದು", "ಪ್ಯಾಡ್", "ಪೆಡಲ್",
            "ब्रेक", "आवाज", "पैड", "रुक नहीं रही", "पेड़ल", "चीख़",
            "بریک", "آواز", "پیڈ", "بریک پیڈ",
            "ബ്രേക്ക്", "ശബ്ദം", "നിർത്താൻ", "ബ്രേക്ക് പാഡ്",
            "பிரேக்", "சத்தம்", "நிற்கவில்லை", "பிரேக் பேட்",
            "బ్రేక్", "శబ్దం", "ఆగడం లేదు", "బ్రేక్ ప్యాడ్",
            "brake", "brakes", "brake noise", "squeak", "pedal sinking", "brake pads", "rotor"
        ],
        "brake system pads wear fluid hydraulic rotor noise inspection"
    ),
    # Battery & Starting / Electrical
    (
        [
            "ಬ್ಯಾಟರಿ", "ಸ್ಟಾರ್ಟ್", "ಆನ್ ಆಗ್ತಿಲ್ಲ", "ಸೆಲ್ಫ್", "ವೋಲ್ಟೇಜ್",
            "बैटरी", "स्टार्ट नहीं", "करंट", "सेल्फ", "वोल्टेज",
            "بیٹری", "سٹارٹ نہیں", "کرنٹ", "وولٹیج",
            "ബാറ്ററി", "സ്റ്റാർട്ട് ആകുന്നില്ല", "വോൾട്ടേജ്",
            "பேட்டரி", "ஸ்டார்ட் ஆகவில்லை", "மின்னழுத்தம்",
            "బ్యాటరీ", "స్టార్ట్ కావడం లేదు", "వోల్టేజ్",
            "battery", "dead battery", "no start", "cranking", "alternator", "starter"
        ],
        "12v battery health starter motor cranking voltage alternator charging"
    ),
    # Engine Oil & Lubrication
    (
        [
            "ಆಯಿಲ್", "ಎಣ್ಣೆ", "ಲೂಬ್ರಿಕಂಟ್", "ಸರ್ವೀಸ್",
            "तेल", "इंजन ऑयल", "मोबिल", "सर्विस",
            "تیل", "انجن آئل", "سروس",
            "ഓയിൽ", "എഞ്ചിൻ ഓയിൽ", "സർവീസ്",
            "ஆயில்", "எஞ்சின் எண்ணெய்", "சர்வீஸ்",
            "ఆయిల్", "ఇంజన్ ఆయిల్", "సర్వీస్",
            "oil", "engine oil", "synthetic oil", "oil change", "oil filter", "lubrication"
        ],
        "engine oil filter change synthetic lubrication viscosity interval"
    ),
    # Check Engine Light / DTC / Misfire
    (
        [
            "ಲೈಟ್", "ಮಿಸ್‌ಫೈರ್", "ವಾರ್ನಿಂಗ್", "ಝರ್ಕ್",
            "चेक इंजन", "बत्ती", "मिसफायर", "झटका",
            "چیک انجن", "روشنی", "جھٹکے",
            "ചെക്ക് എഞ്ചിൻ", "ലൈറ്റ്", "വിറയൽ",
            "செக் என்ஜின்", "லைட்", "அதிர்வு",
            "చెక్ ఇంజన్", "లైట్", "జెర్క్",
            "check engine", "engine light", "misfire", "dtc", "p0300", "p0171", "shudder"
        ],
        "check engine light diagnostic trouble code misfire spark plug ignition"
    ),
    # Transmission & Clutch
    (
        [
            "ಕ್ಲಚ್", "ಗೇರ್", "ಸ್ಲಿಪ್",
            "क्लच", "गियर", "फिसलना",
            "کلچ", "گیئر", "سلپ",
            "ക്ലച്ച്", "ഗിയർ",
            "கிளட்ச்", "கியர்",
            "క్లచ్", "గేర్",
            "clutch", "gearbox", "transmission", "slipping", "atf", "cvt"
        ],
        "transmission clutch disc pressure plate gear slipping fluid replacement"
    ),
    # Smoke & Emissions
    (
        [
            "ಹೊಗೆ", "ಕಪ್ಪು ಹೊಗೆ", "ಬಿಳಿ ಹೊಗೆ",
            "धुआं", "काला धुआं", "सफेद धुआं",
            "دھواں", "کالا دھواں", "سفید دھواں",
            "പുക", "കറുത്ത പുക", "വെള്ള പുക",
            "புகை", "கருப்பு புகை", "வெள்ளை புகை",
            "పొగ", "నల్ల పొగ", "తెల్ల పొగ",
            "smoke", "black smoke", "white smoke", "blue smoke", "exhaust"
        ],
        "exhaust tailpipe smoke rich mixture head gasket oil burning emissions"
    )
]


def normalize_automotive_query(query: str, detected_language: str = "en") -> str:
    """
    Normalizes input query from any of the 7 supported languages to enriched English automotive terms.
    If the query is already in English, returns the cleaned query string.
    """
    if not query or not query.strip():
        return ""

    query_str = query.strip()
    query_lower = query_str.lower()

    # Search for matches across vernacular keywords
    matched_enrichments = []
    for keywords, technical_context in MULTILINGUAL_AUTOMOTIVE_MAP:
        for kw in keywords:
            if kw.lower() in query_lower:
                if technical_context not in matched_enrichments:
                    matched_enrichments.append(technical_context)
                break

    if matched_enrichments:
        # Combine original query with enriched technical terms for comprehensive semantic retrieval
        return f"{query_str} {' '.join(matched_enrichments[:2])}"

    return query_str
