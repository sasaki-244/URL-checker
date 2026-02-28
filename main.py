import re
from urllib.parse import urlparse

from fastapi import FastAPI
from pydantic import BaseModel

# FastAPIアプリ本体。`uvicorn main:app --reload` で起動される。
app = FastAPI(title="URL Checker API")


class ExtractUrlsRequest(BaseModel):
    text: str


class UrlCheckRequest(BaseModel):
    input_type: str
    input: str
    selected_url: str | None = None
    client_ts: str | None = None


def extract_http_urls(text: str) -> list[str]:
    """
    本文から http/https のURLを抽出する最小関数。
    同じURLが複数回出ても、最初の出現だけを返す。
    """
    raw_urls = re.findall(r"https?://[^\s<>()\"']+", text)
    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in raw_urls:
        cleaned = url.rstrip(".,;:!?)")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_urls.append(cleaned)
    return unique_urls


def extract_domain(url: str) -> str:
    """
    URLからドメイン表示用のホストを取り出す。
    パースできない場合は空文字を返す。
    """
    return urlparse(url).netloc


@app.get("/health")
def health() -> dict[str, str]:
    """
    サービスが起動しているかだけを返す最小エンドポイント。
    後続の実装（認証・URL判定）前の動作確認に使う。
    """
    return {"status": "ok"}


@app.post("/v1/extract-urls")
def extract_urls(request: ExtractUrlsRequest) -> dict[str, list[str]]:
    """
    URL抽出APIの最小実装。
    現時点では http/https のみ対象にする。
    """
    return {"candidate_urls": extract_http_urls(request.text)}


@app.post("/v1/url-check")
def url_check(request: UrlCheckRequest) -> dict[str, str | list[str]]:
    """
    URL判定APIの最小版。
    まだ判定実装は行わず、レスポンス形式を固める。
    """
    target_url = request.selected_url or request.input
    return {
        "status": "unknown",
        "domain": extract_domain(target_url),
        "normalized_url": target_url,
        "reason_codes": ["network_error"],
        "candidate_urls": [],
        "message": "Judgement is not available yet.",
        "open_recommendation": "warn",
    }
