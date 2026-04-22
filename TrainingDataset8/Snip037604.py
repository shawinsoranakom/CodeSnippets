def serialize(self, v: Any) -> List[Any]:
        range_value = isinstance(v, (list, tuple))
        value = list(v) if range_value else [v]
        if self.data_type == SliderProto.DATE:
            value = [_datetime_to_micros(_date_to_datetime(v)) for v in value]
        if self.data_type == SliderProto.TIME:
            value = [_datetime_to_micros(_time_to_datetime(v)) for v in value]
        if self.data_type == SliderProto.DATETIME:
            value = [_datetime_to_micros(v) for v in value]
        return value