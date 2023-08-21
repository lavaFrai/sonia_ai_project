import json
from typing import Union, Dict, Optional, List, Tuple, AnyStr, Any, cast

from aiogram.fsm.state import State
from models.state import State as DbState
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

from utils.aiogram_storage_keybuilder import KeyBuilder


class SQLiteStorage(BaseStorage):
    def __init__(self):
        self.key_builder: KeyBuilder = KeyBuilder()

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        key = self.key_builder.build(key, "state")
        if state is None:
            data = DbState.get_or_none(key=key)
            if data is not None:
                data.delete_instance()
        else:
            data = cast(str, state.state if isinstance(state, State) else state)
            row = DbState.get_or_create(key=key)[0]
            row.value = data
            row.save()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        key = self.key_builder.build(key, "state")
        data = DbState.get_or_none(key=key)
        if data is None:
            return None
        return data.value

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        key = self.key_builder.build(key, "data")
        value = data
        data = None
        if not value:
            data = DbState.get_or_none(key=key)
            if data is not None:
                data.delete_instance()
        else:
            row = DbState.get_or_create(key=key)[0]
            row.value = json.dumps(value)
            row.save()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        key = self.key_builder.build(key, "data")
        data = DbState.get_or_none(key=key)
        if data is None:
            return {}
        return json.loads(data.value)

    async def close(self) -> None:
        pass
