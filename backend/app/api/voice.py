"""
AutoAssist AI - Multilingual Voice Synthesis and Transcription API Router
Provides server-side Text-to-Speech (TTS) using gTTS and Speech-to-Text (STT) fallbacks
supporting all 7 target languages: English, Kannada, Hindi, Urdu, Malayalam, Tamil, Telugu.
"""
import io
import logging
from typing import Optional, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, status, Response
from fastapi.responses import JSONResponse
from gtts import gTTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Multilingual Voice Engine"])

# Language mapping for gTTS engine and speech recognition
SUPPORTED_TTS_LANGUAGES = {
    "en": {"code": "en", "name": "English", "tld": "com", "bcp47": "en-IN"},
    "kn": {"code": "kn", "name": "Kannada", "tld": "co.in", "bcp47": "kn-IN"},
    "hi": {"code": "hi", "name": "Hindi", "tld": "co.in", "bcp47": "hi-IN"},
    "ur": {"code": "ur", "name": "Urdu", "tld": "com", "bcp47": "ur-IN"},
    "ml": {"code": "ml", "name": "Malayalam", "tld": "co.in", "bcp47": "ml-IN"},
    "ta": {"code": "ta", "name": "Tamil", "tld": "co.in", "bcp47": "ta-IN"},
    "te": {"code": "te", "name": "Telugu", "tld": "co.in", "bcp47": "te-IN"},
}

# High-performance in-memory cache for synthesized audio bytes
_audio_cache: Dict[str, bytes] = {}


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize into speech")
    lang: Optional[str] = Field("en", description="Target language: en, kn, hi, ur, ml, ta, te")


def _generate_speech_audio(text: str, lang: str = "en") -> Response:
    lang_clean = (lang or "en").lower().strip()
    if lang_clean not in SUPPORTED_TTS_LANGUAGES:
        lang_clean = "en"

    # Clean input text: remove markdown symbols, URLs, asterisks, emoji
    cleaned_text = (
        text.replace("#", "")
        .replace("*", "")
        .replace("`", "")
        .replace("_", "")
        .replace("~", "")
        .replace("₹", " Rupees ")
        .replace("⚠️", " Warning. ")
        .replace("🛑", " Danger. ")
        .replace("💡", "")
        .replace("🔍", "")
        .replace("🔧", "")
        .strip()
    )

    if not cleaned_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty after formatting."
        )

    # Limit text length per synthesis request to ensure low latency
    if len(cleaned_text) > 1500:
        cleaned_text = cleaned_text[:1500]

    cache_key = f"{lang_clean}:{cleaned_text}"
    if cache_key in _audio_cache:
        audio_bytes = _audio_cache[cache_key]
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=speech_{lang_clean}.mp3",
                "Content-Type": "audio/mpeg",
                "Content-Length": str(len(audio_bytes)),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=86400",
                "X-Audio-Cache": "HIT"
            }
        )

    try:
        cfg = SUPPORTED_TTS_LANGUAGES[lang_clean]
        tts = gTTS(text=cleaned_text, lang=cfg["code"], tld=cfg.get("tld", "com"))
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        audio_bytes = buffer.getvalue()

        # Cache synthesized audio (cap cache size to 500 entries)
        if len(_audio_cache) > 500:
            _audio_cache.clear()
        _audio_cache[cache_key] = audio_bytes

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=speech_{lang_clean}.mp3",
                "Content-Type": "audio/mpeg",
                "Content-Length": str(len(audio_bytes)),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=86400",
                "X-Audio-Cache": "MISS"
            }
        )
    except Exception as e:
        logger.error("gTTS speech synthesis failed for lang '%s': %s", lang_clean, e, exc_info=True)
        # Fallback to English synthesis if specific regional dialect failed
        if lang_clean != "en":
            try:
                tts = gTTS(text=cleaned_text, lang="en")
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                audio_bytes = buffer.getvalue()
                return Response(
                    content=audio_bytes,
                    media_type="audio/mpeg",
                    headers={
                        "Content-Disposition": "inline; filename=speech_fallback_en.mp3",
                        "Content-Type": "audio/mpeg",
                        "Content-Length": str(len(audio_bytes)),
                        "Accept-Ranges": "bytes"
                    }
                )
            except Exception as fallback_e:
                logger.error("Fallback English synthesis also failed: %s", fallback_e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {str(e)}"
        )


@router.get(
    "/synthesize",
    summary="Synthesize speech audio for text (GET)",
    description="Streams MP3 audio for the given text in English, Kannada, Hindi, Urdu, Malayalam, Tamil, or Telugu."
)
async def synthesize_speech_get(
    text: str = Query(..., min_length=1, description="Text to speak"),
    lang: str = Query(default="en", description="Target language: en, kn, hi, ur, ml, ta, te")
):
    return _generate_speech_audio(text=text, lang=lang)


@router.post(
    "/synthesize",
    summary="Synthesize speech audio for text (POST JSON)",
    description="Accepts JSON payload with text and language, returns MP3 audio stream without URL length limits."
)
async def synthesize_speech_post(request: SynthesizeRequest):
    return _generate_speech_audio(text=request.text, lang=request.lang)


@router.post(
    "/transcribe",
    summary="Server-side Speech-to-Text (STT) fallback",
    description="Transcribes audio or receives uploaded audio notes in supported languages."
)
async def transcribe_audio(
    audio: Optional[UploadFile] = File(None),
    text_fallback: Optional[str] = Form(None),
    lang: str = Form(default="en")
):
    """
    Server-side STT fallback for browsers without Web Speech API or for recorded audio blobs.
    Accepts audio data (PCM WAV, etc.) or text fallback and returns the recognized spoken words.
    """
    lang_clean = lang.lower().strip()
    cfg = SUPPORTED_TTS_LANGUAGES.get(lang_clean, SUPPORTED_TTS_LANGUAGES["en"])
    bcp47_locale = cfg.get("bcp47", "en-IN")

    if text_fallback:
        return JSONResponse(
            status_code=200,
            content={
                "transcription": text_fallback.strip(),
                "language": lang_clean,
                "locale": bcp47_locale,
                "engine": "text_fallback"
            }
        )

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either an audio file or text_fallback must be provided."
        )

    content = await audio.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty."
        )

    # Attempt SpeechRecognition transcription on audio stream (PCM WAV)
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()

        audio_file = io.BytesIO(content)
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                recognized_text = recognizer.recognize_google(audio_data, language=bcp47_locale)
                if recognized_text and recognized_text.strip():
                    return JSONResponse(
                        status_code=200,
                        content={
                            "transcription": recognized_text.strip(),
                            "language": lang_clean,
                            "locale": bcp47_locale,
                            "engine": "speech_recognition_google"
                        }
                    )
        except sr.UnknownValueError:
            logger.info("Google Speech recognition could not understand audio stream")
            return JSONResponse(
                status_code=200,
                content={
                    "transcription": "",
                    "error": "Could not recognize words. Please speak clearly into the microphone.",
                    "language": lang_clean,
                    "locale": bcp47_locale,
                    "engine": "speech_recognition_google"
                }
            )
        except Exception as stt_err:
            logger.warning("Direct speech recognition on stream error: %s", stt_err)
    except Exception as e:
        logger.warning("speech_recognition library not available or failed: %s", e)

    return JSONResponse(
        status_code=200,
        content={
            "transcription": "",
            "error": "Could not recognize audio. Please speak clearly.",
            "language": lang_clean,
            "locale": bcp47_locale,
            "engine": "server_audio_receiver",
            "bytes_received": len(content)
        }
    )


@router.get(
    "/languages",
    summary="List supported multilingual speech synthesis & recognition languages"
)
async def list_voice_languages():
    return {
        "supported_languages": SUPPORTED_TTS_LANGUAGES,
        "locales": {k: v["bcp47"] for k, v in SUPPORTED_TTS_LANGUAGES.items()}
    }
