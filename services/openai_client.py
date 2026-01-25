import os
import json
import base64
import re
from typing import Any, Dict, Optional

from openai import OpenAI

# 환경변수에서 키 로드 (Railway Variables에 OPENAI_API_KEY 넣어둔 전제)
_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    # 서버 부팅 단계에서 바로 죽지 않게 하고, 호출 시 명확히 에러를 내도록 처리할 수도 있음.
    # 하지만 "분석 API를 누르면 500으로 알려주는" 쪽이 디버깅이 쉬움.
    pass

_client = OpenAI(api_key=_api_key) if _api_key else None


_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def _safe_json_extract(text: str) -> Optional[Dict[str, Any]]:
    """
    모델이 ```json {...} ``` 또는 설명 + {...} 형태로 섞어서 내도
    첫 번째 JSON object를 최대한 복구한다.
    """
    if not text:
        return None

    # 1) 코드블록 제거
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "```").replace("```JSON", "```")
    if "```" in cleaned:
        # 코드블록 안쪽을 우선 사용
        parts = cleaned.split("```")
        # ``` 사이에 들어있는 내용 후보들 중 JSON object가 있는 것 선택
        for p in parts:
            m = _JSON_OBJ_RE.search(p)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass

    # 2) 전체에서 JSON object 찾기
    m = _JSON_OBJ_RE.search(cleaned)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    return None


def analyze_food_text(text: str) -> Dict[str, Any]:
    if not _client:
        raise RuntimeError("OPENAI_API_KEY is not set")

    prompt = f"""
너는 영양 분석기다.
사용자가 입력한 음식 텍스트를 바탕으로 아래 JSON 형식으로만 답해라.

반드시 JSON만 출력:
{{
  "description": "요약",
  "calories_kcal": 0,
  "protein_g": 0,
  "confidence": 0.0,
  "notes": "추정 근거/가정"
}}

음식: {text}
""".strip()

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return ONLY a single JSON object. No markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""
    data = _safe_json_extract(content)

    if not data:
        # 파싱 실패 시에도 API contract 유지
        return {
            "description": "Unparsed response",
            "calories_kcal": 0.0,
            "protein_g": 0.0,
            "confidence": 0.1,
            "notes": content,
        }

    # 타입 강제/기본값
    return {
        "description": str(data.get("description", ""))[:500],
        "calories_kcal": float(data.get("calories_kcal", 0.0) or 0.0),
        "protein_g": float(data.get("protein_g", 0.0) or 0.0),
        "confidence": float(data.get("confidence", 0.5) or 0.5),
        "notes": str(data.get("notes", ""))[:2000],
    }


def analyze_food_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    클라이언트가 파일 업로드로 보낸 바이너리를 그대로 받는 버전.
    """
    if not _client:
        raise RuntimeError("OPENAI_API_KEY is not set")

    b64 = base64.b64encode(image_bytes).decode("utf-8")

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return ONLY a single JSON object. No markdown."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "사진 속 음식을 영양 추정해서 JSON만 출력해라."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            },
        ],
        temperature=0.2,
    )

    content = resp.choices[0].message.content or ""
    data = _safe_json_extract(content)

    if not data:
        return {
            "description": "Unparsed response",
            "calories_kcal": 0.0,
            "protein_g": 0.0,
            "confidence": 0.1,
            "notes": content,
        }

    return {
        "description": str(data.get("description", ""))[:500],
        "calories_kcal": float(data.get("calories_kcal", 0.0) or 0.0),
        "protein_g": float(data.get("protein_g", 0.0) or 0.0),
        "confidence": float(data.get("confidence", 0.5) or 0.5),
        "notes": str(data.get("notes", ""))[:2000],
    }
