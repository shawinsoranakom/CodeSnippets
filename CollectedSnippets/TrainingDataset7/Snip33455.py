def __class_getitem__(cls, key):
                from types import GenericAlias

                return GenericAlias(cls, key)