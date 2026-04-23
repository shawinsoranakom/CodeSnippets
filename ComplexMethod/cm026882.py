def wilight_trigger(value: Any) -> str | None:
    """Check rules for WiLight Trigger."""
    step = 1
    err_desc = "Value is None"
    result_128 = False
    result_24 = False
    result_60 = False
    result_2 = False

    if value is not None:
        step = 2
        err_desc = "Expected a string"

    if (step == 2) & isinstance(value, str):
        step = 3
        err_desc = "String should only contain 8 decimals character"
        if len(value) == 8 and value.isdigit():
            step = 4
            err_desc = "First 3 character should be less than 128"
            result_128 = int(value[0:3]) < 128
            result_24 = int(value[3:5]) < 24
            result_60 = int(value[5:7]) < 60
            result_2 = int(value[7:8]) < 2

    if (step == 4) & result_128:
        step = 5
        err_desc = "Hour part should be less than 24"

    if (step == 5) & result_24:
        step = 6
        err_desc = "Minute part should be less than 60"

    if (step == 6) & result_60:
        step = 7
        err_desc = "Active part should be less than 2"

    if (step == 7) & result_2:
        return value

    raise vol.Invalid(err_desc)