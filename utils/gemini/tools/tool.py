from abc import ABC, abstractmethod


class Tool(ABC):
    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_description(self):
        pass

    @abstractmethod
    def get_parameters(self):
        pass

    @abstractmethod
    async def __call__(self, params: dict):
        pass