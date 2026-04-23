def default(self, o: Any) -> Any:
        if isinstance(o, set):
            return list(o)
        if isinstance(o, datetime.datetime):
            return o.strftime(f"{self.DATE_FORMAT} {self.TIME_FORMAT}")
        if isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        if isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, defer.Deferred):
            return str(o)
        if isinstance(o, Request):
            return f"<{type(o).__name__} {o.method} {o.url}>"
        if isinstance(o, Response):
            return f"<{type(o).__name__} {o.status} {o.url}>"
        if is_item(o):
            return ItemAdapter(o).asdict()
        return super().default(o)