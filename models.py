from sqlalchemy import String, Float, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from db import Base


class MealLog(Base):
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # JWT의 sub를 user_id로 사용
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    email: Mapped[str] = mapped_column(String(256), default="", index=True)

    # 캘린더 기준 (YYYY-MM-DD) 문자열 저장
    meal_date: Mapped[str] = mapped_column(String(10), index=True)

    # 원본 입력
    input_type: Mapped[str] = mapped_column(String(16))   # "text" | "image"
    input_text: Mapped[str] = mapped_column(Text, default="")

    # 분석 결과
    description: Mapped[str] = mapped_column(Text, default="")
    calories_kcal: Mapped[float] = mapped_column(Float, default=0.0)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")
    warnings: Mapped[str] = mapped_column(Text, default="")  # JSON string

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


Index("ix_meal_logs_user_date", MealLog.user_id, MealLog.meal_date)
