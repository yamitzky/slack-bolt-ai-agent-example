# slack-boltのexampleコードを参考にしている: https://github.com/seratch/bolt-python/blob/assistant-apps/examples/assistants/async_interaction_app.py
import asyncio
import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv
from slack_bolt.async_app import (
    AsyncApp,
    AsyncAssistant,
    AsyncSay,
    AsyncSetStatus,
    AsyncSetSuggestedPrompts,
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
if GEMINI_API_KEY := os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=GEMINI_API_KEY)


app = AsyncApp(
    token=SLACK_BOT_TOKEN,
    # This must be set to handle bot message events
    ignoring_self_assistant_message_events_enabled=False,
)


assistant = AsyncAssistant()
# You can use your own thread_context_store if you want
# from slack_bolt.slack_sdk_assistant.thread_context_store import FileAssistantThreadContextStore
# assistant = Assistant(thread_context_store=FileAssistantThreadContextStore())

# NOTICE: もっと高度なSlackボットを作りたい人はこちらの Interaction 機能を使ったサンプルがおすすめです
# https://github.com/slackapi/bolt-python/blob/e6ef608504258b7584909d6b1b7c9fdaeb64b2bc/examples/assistants/async_interaction_app.py


@assistant.thread_started
async def start_thread(say: AsyncSay, set_suggested_prompts: AsyncSetSuggestedPrompts):
    await say(text=":wave: 今日はどうされましたか？")
    await set_suggested_prompts(
        prompts=[
            "こんにちは",
            # 最大４つまで指定できる
        ]
    )


# キーワードに引っ掛けて処理できる
@assistant.user_message(matchers=[lambda body: "こんにちは" in body["event"]["text"]])  # type: ignore
async def find_help_pages(
    payload: dict,
    logger: logging.Logger,
    set_title: AsyncSetTitle,
    set_status: AsyncSetStatus,
    say: AsyncSay,
):
    try:
        await set_title(payload["text"])
        await set_status("入力中...")
        await asyncio.sleep(0.5)
        await say("こんにちは！こんにちは！")
    except Exception as e:
        logger.exception(f"Failed to respond to an inquiry: {e}")
        await say(f":warning: リクエストの処理中にエラーが発生しました (エラー: {e})")


@assistant.user_message
async def respond_to_user_messages(
    logger: logging.Logger,
    set_status: AsyncSetStatus,
    say: AsyncSay,
    payload: dict,
    client: AsyncWebClient,
):
    try:
        await set_status("入力中...")
        if GEMINI_API_KEY:
            # SlackのAPIで過去のの会話履歴を取ってくる
            replies = await client.conversations_replies(
                channel=payload["channel"], ts=payload["thread_ts"]
            )
            history = []
            for message in replies["messages"]:
                if message.get("subtype") == "assistant_app_thread":
                    # 会話の開始は取り除く
                    continue
                is_bot = bool(message.get("bot_id"))
                if text := message.get("text"):
                    history.append(
                        {"role": "model" if is_bot else "user", "parts": text}
                    )
            history = history[1:-1]  # 最初と最後のメッセージは抜く

            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=(
                    "Slackのbotとして、ユーザーの問い合わせに対してサポートをしてください。\n"
                    "出力にはMarkdown形式を使ってはいけません。\n"
                    "リストは - の記号から始めてください。\n"
                    "リンクは <http://www.example.com|This message *is* a link>　のような形式です。\n"
                    "強調表示は *bold* のように囲ってください。決して二重の ** で囲ってはいけません。\n"
                    "コードブロックは ``` で囲ってください。 ```python のような言語指定ブロックは使えません。\n"
                    "それ以外の記号に装飾は絶対に使ってはいけません。"
                ),
            )
            chat = model.start_chat(history=history)
            response = await chat.send_message_async(payload["text"])
            await say(response.text)
        else:
            await say(
                "すみません、コメントの意味がわかりませんでした。別の言い方で教えてください。(ヒント：GEMINI_API_KEYを設定してください)"
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
