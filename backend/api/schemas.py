from typing import Literal
from pydantic import BaseModel, Field, SecretStr, field_validator
from urllib.parse import urlsplit
import re


class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    zone: list[tuple[float, float]] = Field(default_factory=list, max_length=30)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be blank")
        return v.strip()

    @field_validator("zone")
    @classmethod
    def polygon(cls, v):
        if v and len(v) < 3:
            raise ValueError("A zone needs at least three points")
        if any(not 0 <= n <= 1 for p in v for n in p):
            raise ValueError("Zone coordinates must be between 0 and 1")
        return v


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    clues: list[str] = Field(default_factory=list)
    camera_id: str | None = None
    video_id: str | None = None
    object_type: (
        Literal[
            "person",
            "car",
            "truck",
            "bus",
            "motorcycle",
            "bicycle",
            "backpack",
            "handbag",
            "suitcase",
        ]
        | None
    ) = None
    color: (
        Literal[
            "red",
            "orange",
            "yellow",
            "green",
            "cyan",
            "blue",
            "purple",
            "pink",
            "black",
            "white",
            "gray",
            "brown",
        ]
        | None
    ) = None
    min_relevance: float = Field(default=0.15, ge=0, le=1)

    @field_validator("query")
    @classmethod
    def clean_query(cls, v):
        if not v.strip():
            raise ValueError("Enter a search description")
        return v.strip()


class ClipRequest(BaseModel):
    video_id: str
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    context: bool = True


class LiveConnect(BaseModel):
    url: SecretStr
    source_type: Literal["rtsp", "http", "usb"] = "rtsp"
    duration_minutes: int = Field(default=60, ge=1, le=480)

    @field_validator("url")
    @classmethod
    def stream_url(cls, value):
        raw = value.get_secret_value()
        try:
            parsed = urlsplit(raw)
            _ = parsed.port
            valid = (
                (
                    parsed.scheme in ("rtsp", "rtsps", "http", "https")
                    and parsed.hostname
                    and not parsed.fragment
                )
                or raw.isdigit()
                or bool(re.fullmatch(r"/dev/video\d+", raw))
                or (not parsed.scheme and bool(re.fullmatch(r"[a-zA-Z0-9_\-\. ]+", raw)))
            )
        except ValueError:
            valid = False
        if (
            not valid
            or (parsed.scheme and any(c.isspace() for c in raw))
            or len(raw) > 2048
        ):
            raise ValueError(
                "Enter a valid camera stream URL or select a local USB device."
            )
        return value


class AlertUpdate(BaseModel):
    status: Literal["NEW", "REVIEWED", "DISMISSED"]
