from typing import Dict, Any, List, Optional
from collections import defaultdict
import asyncio
from fastapi import APIRouter, HTTPException, Query
from src.common.logger import get_logger
from src.config.config import global_config
from src.plugin_system.apis import message_api, person_api

logger = get_logger("HTTP消息API")
router = APIRouter()

def get_time_range(days: int) -> tuple[float, float]:
    end_time = time.time()
    start_time = end_time - (days * 24 * 3600)
    return start_time, end_time

async def get_messages_filtered(messages: list, bot_qq: str, include_bot: bool = True):
    return [msg for msg in messages if (msg.get("user_id") == bot_qq) == include_bot]

async def format_chat_stats(
    stats: dict,
    chat_manager,
    group_by_user: bool,
):
    formatted = {}
    for chat_id, data in stats.items():
        stream = chat_manager.streams.get(chat_id)
        chat_name = f"未知会话 ({chat_id})"
        if stream:
            if stream.group_info and stream.group_info.group_name:
                chat_name = stream.group_info.group_name
            elif stream.user_info and stream.user_info.user_nickname:
                chat_name = stream.user_info.user_nickname

        result = {"chat_name": chat_name, "total_stats": data["total_stats"]}

        if group_by_user and "user_stats" in data:
            user_stats = {}
            for user_id, count in data["user_stats"].items():
                person_id = person_api.get_person_id("qq", user_id)
                nickname = await person_api.get_person_value(person_id, "nickname", "未知用户")
                user_stats[user_id] = {"nickname": nickname, "count": count}
            result["user_stats"] = user_stats

        formatted[chat_id] = result

    return formatted

@router.get("/messages/recent")
async def get_message_stats(
    days: int = Query(1, ge=1),
    message_type: Literal["all", "sent", "received"] = Query("all"),
):
    try:
        start_time, end_time = get_time_range(days)
        messages = await message_api.get_messages_by_time(start_time, end_time)
        bot_qq = str(global_config.bot.qq_account)

        sent_count = sum(1 for msg in messages if msg.get("user_id") == bot_qq)
        received_count = len(messages) - sent_count

        if message_type == "sent":
            return {"days": days, "message_type": message_type, "count": sent_count}
        elif message_type == "received":
            return {"days": days, "message_type": message_type, "count": received_count}
        else:
            return {
                "days": days,
                "message_type": message_type,
                "sent_count": sent_count,
                "received_count": received_count,
                "total_count": len(messages),
            }

    except Exception as e:
        logger.error(f"Error in get_message_stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/stats_by_chat")
async def get_message_stats_by_chat(
    days: int = Query(1, ge=1),
    group_by_user: bool = Query(False),
    format: bool = Query(False),
):
    try:
        start_time, end_time = get_time_range(days)
        messages = await message_api.get_messages_by_time(start_time, end_time)
        bot_qq = str(global_config.bot.qq_account)

        messages = await get_messages_filtered(messages, bot_qq, include_bot=False)

        stats = defaultdict(lambda: {"total_stats": {"total": 0}, "user_stats": {}})
        for msg in messages:
            chat_id = msg.get("chat_id", "unknown")
            user_id = msg.get("user_id")
            stats[chat_id]["total_stats"]["total"] += 1
            if group_by_user:
                stats[chat_id]["user_stats"][user_id] = stats[chat_id]["user_stats"].get(user_id, 0) + 1

        if not group_by_user:
            stats = {k: v["total_stats"] for k, v in stats.items()}

        if format:
            chat_manager = get_chat_manager()
            return await format_chat_stats(stats, chat_manager, group_by_user)

        return stats

    except Exception as e:
        logger.error(f"Error in get_message_stats_by_chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/bot_stats_by_chat")
async def get_bot_message_stats_by_chat(
    days: int = Query(1, ge=1),
    format: bool = Query(False),
):
    try:
        start_time, end_time = get_time_range(days)
        messages = await message_api.get_messages_by_time(start_time, end_time)
        bot_qq = str(global_config.bot.qq_account)

        bot_messages = await get_messages_filtered(messages, bot_qq, include_bot=True)

        stats = defaultdict(int)
        for msg in bot_messages:
            chat_id = msg.get("chat_id", "unknown")
            stats[chat_id] += 1

        if format:
            chat_manager = get_chat_manager()
            formatted = {}
            for chat_id, count in stats.items():
                stream = chat_manager.streams.get(chat_id)
                chat_name = f"未知会话 ({chat_id})"
                if stream:
                    if stream.group_info and stream.group_info.group_name:
                        chat_name = stream.group_info.group_name
                    elif stream.user_info and stream.user_info.user_nickname:
                        chat_name = stream.user_info.user_nickname
                formatted[chat_id] = {"chat_name": chat_name, "count": count}
            return formatted

        return dict(stats)

    except Exception as e:
        logger.error(f"Error in get_bot_message_stats_by_chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
