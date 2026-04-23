def validate_date(cls, v):
        """Validate the dates entered."""
        if v is None:
            return None
        if isinstance(v, (list, dateType)):
            return v
        new_dates: list = []
        date_param = v
        if isinstance(date_param, str):
            new_dates = date_param.split(",")
        elif isinstance(date_param, dateType):
            new_dates.append(date_param.strftime("%Y-%m-%d"))
        elif isinstance(date_param, list) and isinstance(date_param[0], dateType):
            new_dates = [d.strftime("%Y-%m-%d") for d in new_dates]
        else:
            new_dates = date_param
        return ",".join(new_dates) if len(new_dates) > 1 else new_dates[0]