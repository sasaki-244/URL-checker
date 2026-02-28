# URL-checker

## Step 1: 最小APIを起動する

1. 依存関係をインストール
```bash
python3 -m pip install -r requirements.txt
```

2. APIを起動
```bash
export URL_CHECKER_API_KEY='your-secret-key'
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
