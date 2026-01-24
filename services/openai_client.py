import os
import base64
from typing import Dict, Any

from openai import OpenAI

# NOTE:
# - 로컬/배포 모두 환경변수 OPENAI_API_KEY가 반드시 있어야 함
# - 없으면 여기서 예외 나고 서버가 크래시함
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Set environment variable OPENAI_API_KEY.")

_client = OpenAI(api_key=OPENAI_API_KEY)


def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


async def analyze_food_text(text: str) -> Dict[str, Any]:
    """
    텍스트 기반 음식 추정.
    반환 포맷은 routers/analyze.py의 response_model에 맞춤.
    """
    prompt = (
        "다음 음식 설명을 바탕으로 칼로리(kcal)와 단백질(g)을 추정해줘.\n"
        "가능하면 수치 2개를 반드시 포함하고, 불확실하면 confidence를 낮게 줘.\n\n"
        f"음식: {text}\n\n"
        "JSON으로만 답해. 스키마:\n"
        "{"
        ' "description": string,'
        ' "calories_kcal": number,'
        ' "protein_g": number,'
        ' "confidence": number,'
        ' "notes": string'
        "}"
    )

    resp = _client.chat.completions.create(
        model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are a precise nutrition estimation assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""

    # 모델이 JSON 외 텍스트를 섞는 경우가 있어서, 최소 방어적으로 파싱 시도
    import json
    try:
        data = json.loads(content)
    except Exception:
        # 파싱 실패 시 매우 보수적 fallback
        data = {
            "description": "Unparsed response",
            "calories_kcal": 0,
            "protein_g": 0,
            "confidence": 0.1,
            "notes": content[:500],
        }

    return {
        "description": str(data.get("description", "")),
        "calories_kcal": _safe_float(data.get("calories_kcal", 0)),
        "protein_g": _safe_float(data.get("protein_g", 0)),
        "confidence": _safe_float(data.get("confidence", 0.2)),
        "notes": str(data.get("notes", "")),
    }


async def analyze_food_image(image_b64: str) -> Dict[str, Any]:
    """
    이미지 기반 음식 추정 (간단 버전).
    - 현재는 "이미지 설명 → 추정" 형태로 처리.
    - 나중에 Vision 모델로 개선 가능.
    """
    # 이미지가 너무 크면 비용/시간 이슈 → 제한 권장
    prompt = (
        "다음은 음식 사진의 base64 인코딩 데이터이다.\n"
        "가능한 한 음식 종류를 추정하고 칼로리(kcal)와 단백질(g)을 추정해줘.\n"
        "JSON으로만 답해. 스키마:\n"
        "{"
        ' "description": string,'
        ' "calories_kcal": number,'
        ' "protein_g": number,'
        ' "confidence": number,'
        ' "notes": string'
        "}\n\n"
        f"image_base64: {image_b64[:2000]}...(truncated)"
    )

    resp = _client.chat.completions.create(
        model=os.getenv("OPENAI_IMAGE_FALLBACK_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are a nutrition assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""
    import json
    try:
        data = json.loads(content)
    except Exception:
        data = {
            "description": "Unparsed response",
            "calories_kcal": 0,
            "protein_g": 0,
            "confidence": 0.1,
            "notes": content[:500],
        }

    return {
        "description": str(data.get("description", "")),
        "calories_kcal": _safe_float(data.get("calories_kcal", 0)),
        "protein_g": _safe_float(data.get("protein_g", 0)),
        "confidence": _safe_float(data.get("confidence", 0.2)),
        "notes": str(data.get("notes", "")),
    }
