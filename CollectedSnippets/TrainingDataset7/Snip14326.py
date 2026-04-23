def U(self):
        "Seconds since the Unix epoch (January 1 1970 00:00:00 GMT)"
        value = self.data
        if not isinstance(value, datetime):
            value = datetime.combine(value, time.min)
        return int(value.timestamp())