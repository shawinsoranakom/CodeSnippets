def write_result(self, value_key: str, value: Any, messages: List[MsgData]) -> None:
        """Write a value and associated messages to the cache, overwriting any existing
        result that uses the value_key.
        """
        raise NotImplementedError