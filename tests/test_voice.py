"""
Tests for AutoAssist AI Multilingual Voice Synthesis, STT Fallback & Diagnostic Localization
Verifies all 7 target languages: English, Kannada, Hindi, Urdu, Malayalam, Tamil, Telugu.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.translation_service import get_translation_service
from backend.app.schemas.explanation import SimpleExplanation

client = TestClient(app)


def test_voice_languages_list():
    """Verify endpoint lists all 7 target languages with valid locales."""
    response = client.get("/api/voice/languages")
    assert response.status_code == 200
    data = response.json()
    assert "supported_languages" in data
    assert "locales" in data

    expected_langs = ["en", "kn", "hi", "ur", "ml", "ta", "te"]
    for lang in expected_langs:
        assert lang in data["supported_languages"], f"Missing language {lang}"
        assert lang in data["locales"], f"Missing locale for {lang}"


@pytest.mark.parametrize("lang,text", [
    ("en", "Engine temperature is running hot in traffic."),
    ("kn", "ಎಂಜಿನ್ ತಾಪಮಾನ ಹೆಚ್ಚಾಗಿದೆ."),
    ("hi", "इंजन का तापमान बहुत अधिक है।"),
    ("ur", "گاڑی کا انجن گرم ہو رہا ہے۔"),
    ("ml", "എഞ്ചിൻ താപനില ഉയർന്നിരിക്കുന്നു."),
    ("ta", "என்ஜின் வெப்பநிலை மிக அதிகமாக உள்ளது."),
    ("te", "ఇంజిన్ ఉష్ణోగ్రత వేడెక్కుతోంది."),
])
def test_voice_synthesis_all_languages(lang, text):
    """Verify server synthesizes valid MP3 audio stream for all 7 languages."""
    response = client.get(f"/api/voice/synthesize?text={text}&lang={lang}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 1000  # Valid MP3 audio bytes

    # Verify second call hits in-memory audio cache
    cached_response = client.get(f"/api/voice/synthesize?text={text}&lang={lang}")
    assert cached_response.status_code == 200
    assert cached_response.headers.get("X-Audio-Cache") == "HIT"


def test_voice_synthesis_post_json():
    """Verify POST /api/voice/synthesize accepts JSON payload without URL length limits."""
    response = client.post(
        "/api/voice/synthesize",
        json={"text": "ನಿಮ್ಮ ಎಂಜಿನ್ ಬಿಸಿಯಾಗುತ್ತಿದೆ.", "lang": "kn"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) > 1000


def test_voice_synthesis_empty_text():
    """Verify 400 Bad Request on empty or symbol-only text."""
    # When text consists only of stripped symbols like '#'
    response = client.get("/api/voice/synthesize?text=%23%23%23&lang=en")
    assert response.status_code == 400

    # When text query parameter is blank
    blank_response = client.get("/api/voice/synthesize?text=&lang=en")
    assert blank_response.status_code in [400, 422]


def test_voice_transcribe_text_fallback():
    """Verify server-side transcription handles text fallback."""
    response = client.post(
        "/api/voice/transcribe",
        data={"text_fallback": "Brake pedal sinking", "lang": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transcription"] == "Brake pedal sinking"
    assert data["engine"] == "text_fallback"


def test_voice_transcribe_wav_upload():
    """Verify server accepts uploaded PCM WAV audio file and does not output placeholder captured string."""
    import io, wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00" * 16000)
    buf.seek(0)
    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("speech.wav", buf, "audio/wav")},
        data={"lang": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    # Ensure it NEVER returns the old placeholder
    assert "Audio successfully captured" not in data.get("transcription", "")


def test_translation_service_domains():
    """Verify TranslationService localizes across domains for all 7 languages."""
    ts = get_translation_service()
    base_explanation = SimpleExplanation(
        what_does_it_mean="English explanation",
        why_does_it_happen="English causes",
        symptoms_you_might_notice=["Symptom 1"],
        what_should_you_do=["Action 1"],
        when_to_visit_mechanic="When needed",
        safety_warnings=["Warning"],
        suggested_mechanic_questions=["Question 1"]
    )

    for lang in ["kn", "hi", "ur", "ml", "ta", "te"]:
        # Overheating
        localized_heat = ts.localize_explanation(base_explanation, "engine overheating coolant leak", target_lang=lang)
        assert localized_heat.what_does_it_mean != "English explanation"

        # Brakes
        localized_brake = ts.localize_explanation(base_explanation, "brake pads grinding noise", target_lang=lang)
        assert localized_brake.what_does_it_mean != "English explanation"

        # Battery
        localized_batt = ts.localize_explanation(base_explanation, "battery clicking won't start", target_lang=lang)
        assert localized_batt.what_does_it_mean != "English explanation"


def test_rag_explain_multilingual():
    """Verify /api/rag/explain returns regional localized explanation."""
    response = client.post(
        "/api/rag/explain",
        json={
            "query": "Engine overheating at idle",
            "top_k": 3,
            "language": "kn"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "simple_explanation" in data
    exp = data["simple_explanation"]
    # Kannada characters should be present
    assert any('\u0C80' <= c <= '\u0CFF' for c in exp["what_does_it_mean"])
