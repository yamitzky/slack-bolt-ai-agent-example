# slack-boltのexampleコードを参考にしている: https://github.com/seratch/bolt-python/blob/assistant-apps/examples/assistants/async_interaction_app.py
import asyncio
import json
import logging
import os
import random

from dotenv import load_dotenv
from slack_bolt.async_app import (
    AsyncAck,
    AsyncApp,
    AsyncAssistant,
    AsyncSay,
    AsyncSetStatus,
    AsyncSetTitle,
)
from slack_sdk.web.async_client import AsyncWebClient

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

if port := os.environ.get("PORT"):
    PORT = int(port)
else:
    PORT = 3000
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN xoxb-**** is not set")
if not os.environ.get("SLACK_SIGNING_SECRET"):
    logging.warning('"SLACK_SIGNING_SECRET" environment variable is not set')

app = AsyncApp(
    token=SLACK_BOT_TOKEN,
    # This must be set to handle bot message events
    ignoring_self_assistant_message_events_enabled=False,
)


assistant = AsyncAssistant()
# You can use your own thread_context_store if you want
# from slack_bolt.slack_sdk_assistant.thread_context_store import FileAssistantThreadContextStore
# assistant = Assistant(thread_context_store=FileAssistantThreadContextStore())


@assistant.thread_started
async def start_thread(say: AsyncSay):
    await say(
        text=":wave: 今日はどうされましたか？",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":wave: 今日はどうされましたか？",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "assistant-generate-random-numbers",
                        "text": {
                            "type": "plain_text",
                            "text": "乱数を生成する",
                        },
                        "value": "1",
                    },
                ],
            },
        ],
    )


@app.action("assistant-generate-random-numbers")
async def configure_assistant_summarize_channel(
    ack: AsyncAck, client: AsyncWebClient, body: dict
):
    await ack()

    await client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "configure_assistant_summarize_channel",
            "title": {"type": "plain_text", "text": "My Assistant"},
            "submit": {"type": "plain_text", "text": "送信"},
            "close": {"type": "plain_text", "text": "キャンセル"},
            "private_metadata": json.dumps(
                {
                    "channel_id": body["channel"]["id"],
                    "thread_ts": body["message"]["thread_ts"],
                }
            ),
            "blocks": [
                {
                    "type": "input",
                    "block_id": "num",
                    "label": {"type": "plain_text", "text": "出力する乱数の数"},
                    "element": {
                        "type": "static_select",
                        "action_id": "input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "いくつ乱数を生成しますか？",
                        },
                        "options": [
                            {"text": {"type": "plain_text", "text": "5"}, "value": "5"},
                            {
                                "text": {"type": "plain_text", "text": "10"},
                                "value": "10",
                            },
                            {
                                "text": {"type": "plain_text", "text": "20"},
                                "value": "20",
                            },
                        ],
                        "initial_option": {
                            "text": {"type": "plain_text", "text": "5"},
                            "value": "5",
                        },
                    },
                }
            ],
        },
    )


@app.view("configure_assistant_summarize_channel")
async def receive_configure_assistant_summarize_channel(
    ack: AsyncAck, client: AsyncWebClient, payload: dict
):
    await ack()
    num = payload["state"]["values"]["num"]["input"]["selected_option"]["value"]
    thread = json.loads(payload["private_metadata"])
    await client.chat_postMessage(
        channel=thread["channel_id"],
        thread_ts=thread["thread_ts"],
        text=f"{num}個の乱数ですね。少々お待ちください！",
        metadata={
            "event_type": "assistant-generate-random-numbers",
            "event_payload": {"num": int(num)},
        },
    )


@assistant.bot_message
async def respond_to_bot_messages(
    logger: logging.Logger, set_status: AsyncSetStatus, say: AsyncSay, payload: dict
):
    try:
        if (
            payload.get("metadata", {}).get("event_type")
            == "assistant-generate-random-numbers"
        ):
            await set_status("ランダムな数字のリストを生成しています...")
            await asyncio.sleep(1)
            nums: set[str] = set()
            num = payload["metadata"]["event_payload"]["num"]
            while len(nums) < num:
                nums.add(str(random.randint(1, 100)))
            await say(f"こちらです: {', '.join(nums)}")
        else:
            # nothing to do for this bot message
            # If you want to add more patterns here, be careful not to cause infinite loop messaging
            pass

    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")


@assistant.user_message(matchers=[lambda body: "help page" in body["event"]["text"]])  # type: ignore
async def find_help_pages(
    payload: dict,
    logger: logging.Logger,
    set_title: AsyncSetTitle,
    set_status: AsyncSetStatus,
    say: AsyncSay,
):
    try:
        await set_title(payload["text"])
        await set_status("ヘルプページを検索中...")
        await asyncio.sleep(0.5)
        await say(
            "こちらのヘルプページをご確認ください: https://www.example.com/help-page-123"
        )
    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")
        await say(f":warning: リクエストの処理中にエラーが発生しました (エラー: {e})")


@assistant.user_message
async def respond_to_user_messages(
    logger: logging.Logger, set_status: AsyncSetStatus, say: AsyncSay
):
    try:
        await set_status("入力中...")
        await say(
            "すみません、コメントの意味がわかりませんでした。別の言い方で教えてください。"
        )
    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")
        await say(
            f":warning: すみません、リクエストの処理中にエラーが発生しました (エラー: {e})"
        )


app.use(assistant)


@app.event("message")
async def handle_message_in_channels():
    pass  # noop


@app.event("app_mention")
async def handle_non_assistant_thread_messages(say: AsyncSay):
    await say(":wave: DMで対応します！")


def main():
    app.start(port=PORT)


if __name__ == "__main__":
    main()
