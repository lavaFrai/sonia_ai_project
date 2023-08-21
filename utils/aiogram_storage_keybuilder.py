from typing import Literal

from aiogram.fsm.storage.base import StorageKey, DEFAULT_DESTINY


DEFAULT_DESTINY = "default"


class KeyBuilder:
    """
    Simple Redis key builder with default prefix.

    Generates a colon-joined string with prefix, chat_id, user_id,
    optional bot_id and optional destiny.
    """

    def __init__(
        self,
        *,
        prefix: str = "fsm",
        separator: str = ":",
        with_bot_id: bool = False,
        with_destiny: bool = False,
    ) -> None:
        """
        :param prefix: prefix for all records
        :param separator: separator
        :param with_bot_id: include Bot id in the key
        :param with_destiny: include destiny key
        """
        self.prefix = prefix
        self.separator = separator
        self.with_bot_id = with_bot_id
        self.with_destiny = with_destiny

    def build(self, key: StorageKey, part: Literal["data", "state", "lock"]) -> str:
        parts = [self.prefix]
        if self.with_bot_id:
            parts.append(str(key.bot_id))
        parts.append(str(key.chat_id))
        if key.thread_id:
            parts.append(str(key.thread_id))
        parts.append(str(key.user_id))
        if self.with_destiny:
            parts.append(key.destiny)
        elif key.destiny != DEFAULT_DESTINY:
            raise ValueError(
                "Redis key builder is not configured to use key destiny other the default.\n"
                "\n"
                "Probably, you should set `with_destiny=True` in for DefaultKeyBuilder.\n"
                "E.g: `RedisStorage(redis, key_builder=DefaultKeyBuilder(with_destiny=True))`"
            )
        parts.append(part)
        return self.separator.join(parts)
