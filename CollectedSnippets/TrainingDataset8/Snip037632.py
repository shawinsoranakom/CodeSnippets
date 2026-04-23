def serialize(self, v: DateWidgetReturn) -> List[str]:
        to_serialize = list(v) if isinstance(v, (list, tuple)) else [v]
        return [date.strftime(v, "%Y/%m/%d") for v in to_serialize]