# Slack Bolt AI Agent Example

This repository demonstrates how to create a third-party AI agent for Slack
using the new "Agents & Assistants" feature and the Bolt for Python library.

## Features

- Integrates with Slack's new AI agent UI
- Uses Gemini AI through LiteLLM for generating responses
- Maintains conversation history

## Prerequisites

- Python 3.10+
  - Poetry for package management
- Gemini API key
- Slack App with appropriate permissions

## Installation

1. Clone the repository:

```
git clone https://github.com/yamitzky/slack-bolt-ai-agent-example.git
cd slack-bolt-ai-agent-example
```

2. Install dependencies:

```
poetry install
```

3. Set up environment variables:

```
export SLACK_BOT_TOKEN=your_slack_bot_token
export SLACK_SIGNING_SECRET=your_slack_signing_secret
export SLACK_AGENT_MODEL_NAME=gemini/gemini-1.5-flash
export GEMINI_API_KEY=your_gemini_api_key
```

NOTE: This example uses Gemini, but you can easily switch to other AI providers
supported by LiteLLM. Refer to the
[LiteLLM documentation](https://docs.litellm.ai/docs/providers) for
configuration details.

## Usage

Run the Slack AI agent:

```
poetry run slack-ai-agent
```

Expose the local server (for development):

```
cloudflared tunnel --url http://localhost:3000
```

Update the Request URL in your Slack App's Event Subscriptions with the
Cloudflare tunnel URL + `/slack/events`.

## Slack App Manifest Example

```json
{
  "display_information": {
    "name": "<Use your own app name>"
  },
  "features": {
    "app_home": {
      "home_tab_enabled": false,
      "messages_tab_enabled": true,
      "messages_tab_read_only_enabled": false
    },
    "bot_user": {
      "display_name": "<Use your own app name>",
      "always_online": false
    },
    "assistant_view": {
      "assistant_description": "<Describe your assistant>",
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

- This project uses a development branch of Bolt for Python and may require
  updates in the future.
- For production use, deploy to a cloud environment instead of using Cloudflare
  Quick Tunnel.

## License

[MIT License](LICENSE) This README provides a concise overview of your project,
including its features, installation instructions, and usage guidelines. It also
mentions the key dependencies and configuration options. Feel free to adjust any
details as needed.
