# URL-checker

## Step 1: 最小APIを起動する

1. 依存関係をインストール
```bash
python3 -m pip install -r requirements.txt
```

2. APIを起動
```bash
export URL_CHECKER_API_KEY='your-secret-key'
export GOOGLE_SAFE_BROWSING_API_KEY='your-google-api-key'
python3 -m uvicorn main:app --reload
```

3. ブラウザで確認
`http://127.0.0.1:8000/health`

期待される表示:
```json
{"status":"ok"}
```

## Step 2: 認証付きAPIを叩く

`/v1/*` エンドポイントは `Authorization: Bearer <API_KEY>` が必要です。

```bash
curl -X POST 'http://127.0.0.1:8000/v1/extract-urls' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-secret-key' \
  -d '{"text":"check https://example.com"}'
```

## Step 3: テストを実行する

```bash
source venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

## Reason Codes

`/v1/url-check` の主な `reason_codes`:

- `no_url_found`: テキスト入力からURLを抽出できなかった
- `safe_browsing_hit`: Safe Browsingで脅威ヒット
- `safe_browsing_no_hit`: Safe Browsingでヒットなし
- `safe_browsing_config_error`: `GOOGLE_SAFE_BROWSING_API_KEY` 未設定
- `safe_browsing_timeout`: Safe Browsing通信タイムアウト
- `safe_browsing_request_failed`: Safe Browsing通信失敗
- `safe_browsing_parse_failed`: Safe Browsing応答のJSON解析失敗

## URL Check Example

```bash
curl -X POST 'http://127.0.0.1:8000/v1/url-check' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer your-secret-key' \
  -d '{
    "input_type": "url",
    "input": "EXAMPLE.com/path",
    "selected_url": null,
    "client_ts": "2026-03-01T12:00:00+09:00"
  }'
```

レスポンス例（Safe Browsingヒットなしの場合）:

```json
{
  "status": "likely_safe",
  "domain": "example.com",
  "normalized_url": "https://example.com/path",
  "reason_codes": ["safe_browsing_no_hit"],
  "candidate_urls": [],
  "message": "No Safe Browsing threat match was found.",
  "open_recommendation": "allow"
}
```
