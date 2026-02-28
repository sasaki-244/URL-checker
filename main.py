from fastapi import FastAPI

# FastAPIアプリ本体。`uvicorn main:app --reload` で起動される。
app = FastAPI(title="URL Checker API")


@app.get("/health")
def health() -> dict[str, str]:
    """
    サービスが起動しているかだけを返す最小エンドポイント。
    後続の実装（認証・URL判定）前の動作確認に使う。
    """
    return {"status": "ok"}
