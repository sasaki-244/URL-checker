# URL-checker

## Step 1: 最小APIを起動する

1. 依存関係をインストール
```bash
python3 -m pip install -r requirements.txt
```

2. APIを起動
```bash
python3 -m uvicorn main:app --reload
```

3. ブラウザで確認
`http://127.0.0.1:8000/health`

期待される表示:
```json
{"status":"ok"}
```
