import base64
import os
from io import BytesIO
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from openai import OpenAI

# -----------------------------
# Env / Client
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()

if not OPENAI_API_KEY:
    # 서버 부팅은 되게 두되, /analyze 호출 시 에러를 내는 방식도 가능.
    # 여기선 부팅 시점에 명확히 터뜨려서 실수 방지.
    raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI(title="FoodieEat API", version="0.2.0")

# Flutter(Web/Chrome)에서 호출 편하게 (나중에 도메인 좁히면 됨)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

def _image_to_data_url(image_bytes: bytes) -> str:
    """
    업로드된 이미지 bytes를 안전하게 RGB JPEG로 변환 후
    data URL(base64)로 만들어 OpenAI에 전달.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        img = img.convert("RGB")
        out = BytesIO()
        img.save(out, format="JPEG", quality=90)
        b64 = base64.b64encode(out.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

@app.post("/analyze")
async def analyze(
    image: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
):
    """
    multipart/form-data로 받는다.
    - image: 파일 업로드(선택)
    - text: 텍스트(선택)
    단, 둘 중 하나는 반드시 필요.
    """
    text = (text or "").strip()

    if image is None and not text:
        raise HTTPException(status_code=422, detail="image 또는 text 중 하나는 필요합니다.")

    # 입력 구성 (Responses API 포맷)
    # 공식 문서에서 이미지 입력은 content 배열에 input_image로 넣는다. :contentReference[oaicite:1]{index=1}
    user_content = []

    # 텍스트가 있으면 같이 제공
    if text:
        user_content.append({"type": "input_text", "text": f"사용자 입력 음식: {text}\n간단히 분석해줘."})

    # 이미지가 있으면 data URL로 제공
    if image is not None:
        img_bytes = await image.read()
        data_url = _image_to_data_url(img_bytes)
        user_content.append({"type": "input_image", "image_url": data_url})

    # 모델에게 "항상 JSON만" 출력하도록 강제(서버에서 파싱 안정화)
    system_instructions = (
        "너는 음식 입력(텍스트/이미지)을 바탕으로 아주 단순한 건강 피드백을 주는 도우미다.\n"
        "반드시 JSON만 출력해라. 키는 source, recommended_activity_min, message 세 개만 사용해라.\n"
        "- source: 'text' 또는 'image' 또는 'both'\n"
        "- recommended_activity_min: 정수 (예: 30)\n"
        "- message: 한국어 한 문장\n"
        "그 외의 텍스트를 절대 섞지 마라."
    )

    source = "both" if (image is not None and text) else ("image" if image is not None else "text")

    try:
        resp = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_instructions}],
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
        )

        # Responses API는 output_text로 텍스트를 얻을 수 있다. :contentReference[oaicite:2]{index=2}
        raw = (resp.output_text or "").strip()
        if not raw:
            raise HTTPException(status_code=502, detail="Empty response from model")

        # 모델이 JSON만 준다고 가정하고 그대로 반환(프론트에서 jsonDecode)
        # 만약 여기서 더 견고하게 하려면 json.loads 검증을 추가하면 됨.
        return {
            "source": source,
            "recommended_activity_min": 30,
            "message": raw if raw.startswith("{") else "분석 결과를 생성했습니다.",
            "raw": raw,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI call failed: {e}")
