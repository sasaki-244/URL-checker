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

## iOS Shortcut Setup (Share Sheet)

このプロジェクトのiOS側は「ショートカット」だけで実装します。  
入力は共有シートから受け取り、結果は表示のみ行います（`Open URL` / `Copy URL` は実装しない方針）。

事前に必要なもの:

- API公開URL（例: `https://your-app.onrender.com`）
- `URL_CHECKER_API_KEY`

### 1. 共有シートから起動できるショートカットを作る

1. ショートカットアプリで新規作成し、名前を `URLチェック` にする
2. 詳細設定で共有シート表示を有効化
3. 受け取りタイプを `URL` と `テキスト` にする

### 2. 入力分岐を作る

1. `ショートカット入力` をテキスト化
2. `If` で `://` を含むか判定
3. 含む場合は `target_url`（URL入力扱い）、含まない場合は `input_text`（テキスト入力扱い）に保存

### 3. テキスト入力時にURL候補を抽出する

`input_text` 側で `URLの内容を取得` を使って以下を実行:

- `POST /v1/extract-urls`
- ヘッダ:
  - `Content-Type: application/json`
  - `Authorization: Bearer <URL_CHECKER_API_KEY>`
- JSON本文:
  - `text: <input_text>`

レスポンスの `candidate_urls` を取得し、件数で分岐:

- 0件: `Unknown` 表示して終了
- 1件: その1件を `selected_url` にする
- 複数件: メニューで1件選んで `selected_url` にする

### 4. 判定APIを呼ぶ

`URLの内容を取得` で以下を実行:

- `POST /v1/url-check`
- ヘッダ:
  - `Content-Type: application/json`
  - `Authorization: Bearer <URL_CHECKER_API_KEY>`
- JSON本文:
  - `input_type: "url"`
  - `input: <selected_url or target_url>`
  - `selected_url: <selected_url or target_url>`
  - `client_ts: <現在時刻 or 空>`

### 5. 判定結果を表示する（操作なし）

レスポンスから以下を取り出して表示:

- `status`
- `domain`
- `normalized_url`
- `reason_codes`
- `open_recommendation`

表示例:

```text
判定: [status]
ドメイン: [domain]
URL: [normalized_url]
理由: [reason_codes]
推奨: [open_recommendation]
```

注記:

- `Open URL` / `Copy URL` アクションは実装しない
- `status` が `likely_safe` / `suspected` / `unknown` のいずれでも表示のみ

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
