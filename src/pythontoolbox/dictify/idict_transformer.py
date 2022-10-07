from abc import ABC, abstractmethod


class IDictTransformer(ABC):

    @abstractmethod
    def transform_to_dict(self, obj):
        pass
