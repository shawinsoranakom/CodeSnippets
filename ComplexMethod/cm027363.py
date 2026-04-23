def from_dict(cls, restored: dict[str, Any]) -> Self | None:
        """Initialize a stored sensor state from a dict."""
        try:
            native_value = restored["native_value"]
            native_unit_of_measurement = restored["native_unit_of_measurement"]
        except KeyError:
            return None
        try:
            type_ = native_value["__type"]
            if type_ == "<class 'datetime.datetime'>":
                native_value = dt_util.parse_datetime(native_value["isoformat"])
            elif type_ == "<class 'datetime.date'>":
                native_value = dt_util.parse_date(native_value["isoformat"])
            elif type_ == "<class 'decimal.Decimal'>":
                native_value = Decimal(native_value["decimal_str"])
        except TypeError:
            # native_value is not a dict
            pass
        except KeyError:
            # native_value is a dict, but does not have all values
            return None
        except DecimalInvalidOperation:
            # native_value couldn't be returned from decimal_str
            return None

        return cls(native_value, native_unit_of_measurement)