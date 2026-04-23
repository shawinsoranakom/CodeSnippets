def serialize(self, v: Union[datetime, time]) -> str:
        if isinstance(v, datetime):
            v = v.time()
        return time.strftime(v, "%H:%M")