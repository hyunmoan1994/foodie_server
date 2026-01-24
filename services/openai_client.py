# services/openai_client.py
import os
import base64
from typing import Optional, Dict, Any

from openai import OpenAI


# -------------------------
# Lazy client (import 시점에 죽지 않게)
# -------------------------
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """
    OpenAI 클라이언트를 '지연 초기화'한다.
    - 서버 import 시점에 OPENAI_API_KEY 없어도 크래시 안 남
    - 실제 요청 처리 시점에 키가 없으면 명확한 에러로 반환 가능
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Set env var or Railway Variables.")
        _client = OpenAI(api_key=api_key)
    return _client


# -------------------------
# Text analyze
# -------------------------
async def analyze_food_text(text: str) -> Dict[str, Any]:
    """
    입력 텍스트 기반으로 칼로리/단백질 추정.
    routers/analyze.py에서 await로 호출하는 형태에 맞춰 async 유지.
    """
    client = get_client()

    system = "You are a nutrition assistant. Reply in JSON only."
    user = f"""
다음 음식(또는 식사 설명)의 대략적인 영양을 추정해서 JSON으로만 답해줘.

요구 JSON 스키마(반드시 이 키를 포함):
{{
  "description": "짧은 요약",
  "calories_kcal": number,
  "protein_g": number,
  "confidence": number,   // 0.0~1.0
  "notes": "불확실성/가정"
}}

음식: {text}
"""

    # OpenAI Python SDK(v1) - responses API 사용
    resp = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    # responses API 결과 텍스트 추출
    out_text = getattr(resp, "output_text", None)
    if not out_text:
        # 방어 로직
        raise RuntimeError("OpenAI response has no output_text")

    # JSON 문자열을 그대로 반환(routers 쪽에서 pydantic response_model로 매핑 가능)
    # 단, 여기서는 파싱까지 하면 더 안전하지만 현재 구조를 모르니 문자열 기반 사용.
    # routers/analyze.py에서 json.loads를 하고 있으면 그대로 OK.
    return {"raw": out_text}


# -------------------------
# Image analyze
# -------------------------
async def analyze_food_image(image_b64: str) -> Dict[str, Any]:
    """
    base64 인코딩된 이미지(바이너리 -> base64 string)를 입력으로 받아 추정.
    """
    client = get_client()

    system = "You are a nutrition assistant. Reply in JSON only."
    user = """
이미지 속 음식의 대략적인 영양을 추정해서 JSON으로만 답해줘.

요구 JSON 스키마(반드시 이 키를 포함):
{
  "description": "짧은 요약",
  "calories_kcal": number,
  "protein_g": number,
  "confidence": number,   // 0.0~1.0
  "notes": "불확실성/가정"
}
"""

    # image_b64가 순수 base64인지, data URL인지 모두 대응
    if image_b64.startswith("data:"):
        data_url = image_b64
    else:
        data_url = f"data:image/jpeg;base64,{image_b64}"

    resp = client.responses.create(
        model=os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        input=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user},
                    {"type": "input_image", "image_url": data_url},
                ],
            },
        ],
    )

    out_text = getattr(resp, "output_text", None)
    if not out_text:
        raise RuntimeError("OpenAI response has no output_text")

    return {"raw": out_text}
