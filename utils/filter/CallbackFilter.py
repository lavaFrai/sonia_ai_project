from typing import Any, Union, Dict, Optional

from aiogram.filters import Filter
from aiogram.types import CallbackQuery


class CallbackFilter(Filter):
    def __init__(self, data: str = None, starts_with: str = None):
        self.data = data
        self.starts_with = starts_with
        if data is None and starts_with is None:
            raise RuntimeError("Must be some one filter data")

    async def __call__(self, obj: CallbackQuery, raw_state: Optional[str] = None) -> Union[bool, Dict[str, Any]]:
        if self.data is not None:
            return obj.data == self.data
        else:
            return obj.data.startswith(self.starts_with)
