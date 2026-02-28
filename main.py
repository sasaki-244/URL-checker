import re
import os
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException
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


class LocalJudgeResult(BaseModel):
    status: str
    reason_codes: list[str]
    message: str
    open_recommendation: str


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


def is_http_url(value: str) -> bool:
    """
    http/https かつホストを持つURLかを簡易チェックする。
    """
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def verify_api_key(authorization: str | None = Header(default=None)) -> None:
    """
    固定Bearer APIキー認証。
    URL_CHECKER_API_KEY と一致しない場合は 401 を返す。
    """
    expected = os.getenv("URL_CHECKER_API_KEY")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail={"reason_code": "server_error", "message": "URL_CHECKER_API_KEY is not configured."},
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"reason_code": "unauthorized", "message": "Authorization header is required."},
        )
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(
            status_code=401,
            detail={"reason_code": "unauthorized", "message": "Invalid API key."},
        )


def judge_url_locally(url: str) -> LocalJudgeResult:
    """
    ローカル判定の仮実装。
    次ステップで Google Safe Browsing 連携に置き換える。
    """
    _ = url
    return LocalJudgeResult(
        status="likely_safe",
        reason_codes=["local_stub_no_hit"],
        message="No suspicious signal detected by local stub.",
        open_recommendation="allow",
    )


@app.get("/health")
def health() -> dict[str, str]:
    """
    サービスが起動しているかだけを返す最小エンドポイント。
    後続の実装（認証・URL判定）前の動作確認に使う。
    """
    return {"status": "ok"}


@app.post("/v1/extract-urls")
def extract_urls(
    request: ExtractUrlsRequest,
    _: None = Depends(verify_api_key),
) -> dict[str, list[str]]:
    """
    URL抽出APIの最小実装。
    現時点では http/https のみ対象にする。
    """
    return {"candidate_urls": extract_http_urls(request.text)}


@app.post("/v1/url-check")
def url_check(
    request: UrlCheckRequest,
    _: None = Depends(verify_api_key),
) -> dict[str, str | list[str]]:
    """
    URL判定APIの最小版。
    まだ判定実装は行わず、レスポンス形式を固める。
    """
    if request.input_type not in {"url", "text"}:
        raise HTTPException(
            status_code=400,
            detail={"reason_code": "parse_error", "message": "input_type must be 'url' or 'text'."},
        )
    if not request.input.strip():
        raise HTTPException(
            status_code=400,
            detail={"reason_code": "parse_error", "message": "input must not be empty."},
        )

    candidate_urls: list[str] = []
    if request.input_type == "text":
        candidate_urls = extract_http_urls(request.input)
        if not candidate_urls:
            return {
                "status": "unknown",
                "domain": "",
                "normalized_url": "",
                "reason_codes": ["no_url_found"],
                "candidate_urls": [],
                "message": "No URL was found in the input text.",
                "open_recommendation": "warn",
            }
        if request.selected_url and request.selected_url not in candidate_urls:
            raise HTTPException(
                status_code=400,
                detail={"reason_code": "parse_error", "message": "selected_url is not in candidate_urls."},
            )
        target_url = request.selected_url or candidate_urls[0]
    else:
        target_url = request.selected_url or request.input
        if not is_http_url(target_url):
            raise HTTPException(
                status_code=400,
                detail={"reason_code": "parse_error", "message": "input must be a valid http/https URL."},
            )
    judge = judge_url_locally(target_url)

    return {
        "status": judge.status,
        "domain": urlparse(target_url).netloc,
        "normalized_url": target_url,
        "reason_codes": judge.reason_codes,
        "candidate_urls": candidate_urls,
        "message": judge.message,
        "open_recommendation": judge.open_recommendation,
    }
