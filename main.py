import re

from fastapi import FastAPI
from pydantic import BaseModel

# FastAPIアプリ本体。`uvicorn main:app --reload` で起動される。
app = FastAPI(title="URL Checker API")


class ExtractUrlsRequest(BaseModel):
    text: str


def extract_http_urls(text: str) -> list[str]:
    """
    本文から http/https のURLを抽出する最小関数。
    同じURLが複数回出ても、最初の出現だけを返す。
    """
    raw_urls = re.findall(r"https?://[^\s<>()\"']+", text)
    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in raw_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls


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
