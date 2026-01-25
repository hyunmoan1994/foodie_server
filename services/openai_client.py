import os
import json
from typing import Any, Dict
from openai import OpenAI

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _normalize_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    desc = str(payload.get("description", "")).strip()
    calories = _safe_float(payload.get("calories_kcal", 0.0), 0.0)
    protein = _safe_float(payload.get("protein_g", 0.0), 0.0)
    conf = _safe_float(payload.get("confidence", 0.1), 0.1)
    notes = str(payload.get("notes", "")).strip()

    warnings = []
    if conf < 0.5:
        warnings.append("confidence_low")
    if calories <= 0 and protein <= 0:
        warnings.append("nutrition_unknown")

    return {
        "description": desc or "추정 불가",
        "calories_kcal": calories,
        "protein_g": protein,
        "confidence": conf,
        "notes": notes,
        "warnings": warnings,
    }


def analyze_food_text(text: str) -> Dict[str, Any]:
    system = (
        "You are a nutrition estimation engine. "
        "Return ONLY valid JSON object with keys: "
        "description (string, Korean), calories_kcal (number), protein_g (number), confidence (0-1), notes (string, Korean). "
        "Do not wrap in markdown. No code fences."
    )
    user = f"입력 텍스트: {text}\n위 조건에 맞는 JSON만 반환."

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = resp.choices[0].message.content or "{}"
    try:
        payload = json.loads(content)
    except Exception:
        payload = {"description": "Unparsed response", "calories_kcal": 0, "protein_g": 0, "confidence": 0.1, "notes": content}

    return _normalize_result(payload)


def analyze_food_image(image_b64: str) -> Dict[str, Any]:
    system = (
        "You are a nutrition estimation engine for food images. "
        "Return ONLY valid JSON object with keys: "
        "description (string, Korean), calories_kcal (number), protein_g (number), confidence (0-1), notes (string, Korean). "
        "Do not wrap in markdown. No code fences."
    )

    resp = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "사진을 보고 음식과 대략 영양을 추정해서 JSON만 반환."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = resp.choices[0].message.content or "{}"
    try:
        payload = json.loads(content)
    except Exception:
        payload = {"description": "Unparsed response", "calories_kcal": 0, "protein_g": 0, "confidence": 0.1, "notes": content}

    return _normalize_result(payload)
