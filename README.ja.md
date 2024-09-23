# Slack Bolt AI で作る AI エージェント

新しい「Agents & Assistants」機能と Bolt for Python ライブラリを使用して、Slack
のサードパーティ AI エージェントを作成するサンプルプロジェクトです。

解説記事：https://tech.jxpress.net/entry/slack-agents-assistants

## 機能

- Slack の Agents & Assistants に対応
- LiteLLM を介して Gemini AI を使用して応答を生成
- 会話履歴を保持

## 前提条件

- Python 3.10+
  - パッケージマネージャーとして Poetry を利用
- Gemini API キー
- 適切な権限を持つ Slack アプリ

## インストール

1. リポジトリをクローンします。

```
git clone https://github.com/yamitzky/slack-bolt-ai-agent-example.git
cd slack-bolt-ai-agent-example
```

2. 依存関係をインストールします。

```
poetry install
```

3. 環境変数を設定します。

```
export SLACK_BOT_TOKEN=your_slack_bot_token
export SLACK_SIGNING_SECRET=your_slack_signing_secret
export SLACK_AGENT_MODEL_NAME=gemini/gemini-1.5-flash
export GEMINI_API_KEY=your_gemini_api_key
```

注：この例では Gemini を使用していますが、LiteLLM でサポートされている他の AI
プロバイダーに簡単に切り替えることができます。設定の詳細については、
[LiteLLM のドキュメント](https://docs.litellm.ai/docs/providers)
を参照してください。

## 使い方

Slack AI エージェントを実行します。

```
poetry run slack-ai-agent
```

ローカルサーバーを公開します（開発用）。

```
cloudflared tunnel --url http://localhost:3000
```

Slack アプリの「Event Subscription」の URL を、Cloudflare tunnel のURL +
`/slack/events` に更新します。

## Slack アプリマニフェストの例

```json
{
  "display_information": {
    "name": "<ご自身のアプリ名を使用してください>"
  },
  "features": {
    "app_home": {
      "home_tab_enabled": false,
      "messages_tab_enabled": true,
      "messages_tab_read_only_enabled": false
    },
    "bot_user": {
      "display_name": "<ご自身のアプリ名を使用してください>",
      "always_online": false
    },
    "assistant_view": {
      "assistant_description": "<アシスタントの説明>",
      "suggested_prompts": []
    }
  },
  "oauth_config": {
    "scopes": {
      "bot": ["assistant:write", "im:history", "chat:write"]
    }
  },
  "settings": {
    "event_subscriptions": {
      "request_url": "https://*****.example.com/slack/events",
      "bot_events": [
        "assistant_thread_context_changed",
        "assistant_thread_started",
        "message.im"
      ]
    },
    "org_deploy_enabled": false,
    "socket_mode_enabled": false,
    "token_rotation_enabled": false
  }
}
```

## Notes

- このプロジェクトでは、Bolt for Python の Pull Request
  を使用しており、将来変更が必要になる場合があります。
- 本番環境では、Cloudflare Quick Tunnel
  を使用するのではなく、クラウド環境などにデプロイしてください。

## License

[MIT License](https://github.com/yamitzky/slack-bolt-ai-agent-example/blob/main/LICENSE)
