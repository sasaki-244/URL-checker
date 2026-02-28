from fastapi import FastAPI
from pydantic import BaseModel

# FastAPIアプリ本体。`uvicorn main:app --reload` で起動される。
app = FastAPI(title="URL Checker API")


class ExtractUrlsRequest(BaseModel):
    text: str


@app.get("/health")
def health() -> dict[str, str]:
    """
    サービスが起動しているかだけを返す最小エンドポイント。
    後続の実装（認証・URL判定）前の動作確認に使う。
    """
    return {"status": "ok"}


@app.post("/v1/extract-urls")
def extract_urls(_: ExtractUrlsRequest) -> dict[str, list[str]]:
    """
    URL抽出APIの最小版。
    まずは入力を受け取れることだけ確認し、候補は空配列で返す。
    """
    return {"candidate_urls": []}
