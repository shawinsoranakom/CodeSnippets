def typecast_date(s):
    return (
        datetime.date(*map(int, s.split("-"))) if s else None
    )