# Podman Voicevox Engine API
音声合成エンジン Voicevox Engine をPodmanで動かし、API経由で音声合成を行うためのコンテナイメージです。  
Voicevox Engine には無い 機能を追加します。  
- API Key の発行
- CORS用ドメイン登録
- リクエストの簡略化
- MP3,MP4 形式での音声データ取得
- 変換処理を非同期で実行するためのステータスAPI 提供
- podman compose 対応

## 機能詳細

### API Key の発行
APIへのアクセスを認証・管理するためのキーを発行します。初回起動時に環境変数 `ADMIN_API_KEY` で設定した管理者キーを使い、API経由で他のキーを動的に発行・管理できます。

### CORS用ドメイン登録
ブラウザから直接APIを利用できるように、許可するドメイン（オリジン）をAPIキー毎に登録・管理できます。

### リクエストの簡略化
オリジナルのVoicevox Engineでは `/audio_query` と `/synthesis` の2つのAPIを呼び出す必要がありますが、本APIではリクエストを1つにまとめることができます。

### MP3,MP4 形式での音声データ取得
標準のWAV形式に加えて、より汎用的なMP3形式やMP4形式で音声データを取得できます。

### 非同期処理とステータスAPI
長文のテキストを変換する際に便利な非同期処理に対応します。リクエスト後にジョブIDを受け取り、ステータスAPIで変換の進捗や完了を確認できます。

### podman compose 対応
`podman compose` を利用して、簡単にコンテナを起動・管理するための設定ファイルを提供します。

## 使い方 (Usage)

1. **環境変数の設定**

   `.env.sample` ファイルを `.env` という名前でコピーし、`ADMIN_API_KEY` の値を安全なものに変更します。

   ```bash
   cp .env.sample .env
   ```

   `.env` ファイルの例:

   ```
   ADMIN_API_KEY=your_strong_admin_api_key_here
   ```

2. **コンテナのビルドと起動**

   以下のコマンドを実行して、コンテナをビルドし、バックグラウンドで起動します。

   ```bash
   brew install podman-desktop podman-compose
   podman machine set --rootful=false
   podman machine init --now --volume /Volumes/SSD/Podman/
   podman machine info
   podman machine stop
   podman machine start
   podman machine ls

   podman compose build
   podman compose up -d
   ```

3. **APIへのアクセス**

      APIサーバーは `http://localhost:8080` で利用可能になります。

4. **テストの実行**

   コンテナを起動せずに、ローカル環境でテストを実行するには、以下のコマンドを使用します。

   ```bash
   pip install -r requirements.txt
   pytest
   ```

   または、コンテナ内でテストを実行するには、以下のコマンドを使用します。

   ```bash
   podman compose run voicevox-api pytest
   ```


### APIテスト (curl)

まず、`compose.yml`で設定した`ADMIN_API_KEY`、または`/api/admin/keys`で発行したAPIキーを環境変数に設定してください。

```bash
export ADMIN_API_KEY="your_strong_admin_api_key_here" # compose.ymlで設定した管理者キー
export API_KEY="your_generated_api_key_here" # /api/admin/keysで発行したキー
```

#### 1. ヘルスチェック (認証不要)

```bash
curl http://localhost:8080/
```

#### 2. 認証済みルートエンドポイント

```bash
curl -H "X-API-KEY: $API_KEY" http://localhost:8080/api/
```

#### 3. APIキー管理 (管理者キーが必要)

##### 3.1. APIキーの一覧取得

```bash
curl -H "X-API-KEY: $ADMIN_API_KEY" http://localhost:8080/api/admin/keys
```

##### 3.2. 新しいAPIキーの発行

```bash
curl -X POST -H "X-API-KEY: $ADMIN_API_KEY" http://localhost:8080/api/admin/keys

# export API_KEY="$(curl -H "X-API-KEY: $ADMIN_API_KEY" http://localhost:8080/api/admin/keys | jq -r '.[0]')"
# echo "API KEY: $API_KEY"
```

##### 3.3. APIキーの削除 (例: "your_key_to_delete" を削除)

```bash
curl -X DELETE -H "X-API-KEY: $ADMIN_API_KEY" http://localhost:8080/api/admin/keys/your_key_to_delete
```

#### 4. CORSオリジン管理

##### 4.1. CORSオリジンの一覧取得
APIキーに紐づくCORSオリジンの一覧を取得します。

```bash
curl -H "X-API-KEY: $API_KEY" http://localhost:8080/api/origins
```

##### 4.2. CORSオリジンの追加 (例: "http://example.com" を追加)
APIキーにCORSオリジンを紐づけて登録します。

```bash
curl -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" -d '{"origin": "http://example.com"}' http://localhost:8080/api/origins
```

##### 4.3. CORSオリジンの削除 (例: "http://example.com" を削除)
APIキーに紐づくCORSオリジンを削除します。

```bash
curl -X DELETE -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" -d '{"origin": "http://example.com"}' http://localhost:8080/api/origins
```

#### 5. 音声合成 (簡略化されたリクエスト)

```bash
curl -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
     -d '{"text": "こんにちは、ボイスボックスです。", "speaker": 1, "format": "mp3"}' \
     http://localhost:8080/api/synthesis -o temp/output.mp3
```

#### 6. 非同期音声合成

##### 6.1. 音声合成ジョブの送信
`jq` コマンドで `job_id` を取得して、環境変数に設定します。

```bash
export JOB_ID=$(curl -s -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
     -d '{"text": "これは非同期テストです。", "speaker": 1, "format": "wav"}' \
     http://localhost:8080/api/tasks/synthesis | jq -r .job_id)

echo "Job ID: $JOB_ID"
```

##### 6.2. ジョブのステータス確認

```bash
curl -H "X-API-KEY: $API_KEY" http://localhost:8080/api/tasks/$JOB_ID/status
```

##### 6.3. ジョブの結果取得

```bash
curl -H "X-API-KEY: $API_KEY" http://localhost:8080/api/tasks/$JOB_ID/result -o temp/async_output.wav
```

## Google Cloud Run へのデプロイ手順
`gcloud alpha run compose up compose.yml` で Google Cloud Run に簡単にデプロイできます。  

```
gcloud auth login
gcloud config list
gcloud config get-value project
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region asia-northeast1

# デプロイ実行
gcloud alpha run compose up compose.yml

# Cloud Run サービスの確認
# gcloud run services proxy podman-voicevox-api --port=8080
# http://localhost:8080 にアクセス

# サービス削除
# gcloud run services delete podman-voicevox-api
```

デプロイ後 [Cloud Run コンソール セキュリティを変更](https://console.cloud.google.com/run) し 公開アクセスを許可する


## 参考
- [Voicevox Engine GitHub](https://github.com/VoiceVox/VoiceVox)
- [Podman 公式ドキュメント](https://podman.io/getting-started/quick-start)
# podman-voicevox-api
