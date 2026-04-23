def t(*result):
            return "|".join(datetimes[key].isoformat() for key in result)