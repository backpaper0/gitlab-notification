# GitLab Notification

GitLabのTo-Doリストを[Owattayo](https://github.com/backpaper0/owattayo)へ通知する常駐プログラム。

## 機能

- プログラム起動以降に登録されたTo-Doをowattayoへ通知する
- owattayoへ通知する内容は次の通り
    - To-Doの`author.username`と`body`をpromptとして渡す
    - To-Doの`target_url`をurlとして渡す
- `state`が`pending`のTo-Doだけを通知する
- 通知済みのTo-Doの`id`をSQLiteへ記録する
    - `id`はシーケンス（整数値）なので、最大値だけを記録しておけば良い

## 依存関係

- Python 3.12以上
- pydantic-settings 2.10.1以上
- requests 2.32.5以上

## セットアップ

### 環境変数

以下の環境変数を設定するか、`.env`ファイルに記載してください：

```bash
GITLAB_PERSONAL_ACCESS_TOKEN=your_gitlab_token
GITLAB_TODOS_API_ENDPOINT=https://gitlab.com/api/v4/todos
OWATTAYO_API_ENDPOINT=http://localhost:8000/notify
DB_PATH=gitlab-notification.db  # オプション、デフォルト値
INTERVAL_SECONDS=60             # オプション、ポーリング間隔（秒）
```

### ローカル実行

```bash
python main.py
```

### Dockerで実行

```bash
docker build -t gitlab-notification .
docker run -e GITLAB_PERSONAL_ACCESS_TOKEN=your_token \
           -e GITLAB_TODOS_API_ENDPOINT=your_endpoint \
           -e OWATTAYO_API_ENDPOINT=your_owattayo_endpoint \
           gitlab-notification
```

## デプロイ

GitHub Actionsによる自動デプロイが設定されています。

- `v*`形式のタグをプッシュすると、GitHub Container Registryにイメージがビルド・プッシュされます
- イメージ名: `ghcr.io/{owner}/gitlab-notification`

## 実装詳細

- `GitLabNotificationService`クラス（main.py:27-128）がメイン機能を実装
- SQLiteデータベースで処理済みTo-DoのIDを管理（main.py:32-41）
- 設定可能なポーリング間隔でGitLab APIから新しいTo-Doを取得（main.py:54-67）
- Owattayo APIへの通知送信（main.py:69-78）
