def _filter(d: Data) -> bool:
        _date = getattr(d, "date", None)
        dt = _date.date() if _date and isinstance(_date, datetime) else _date
        if dt:
            if start_date and end_date:
                return start_date <= dt <= end_date
            if start_date:
                return dt >= start_date
            if end_date:
                return dt <= end_date
            return True
        return False