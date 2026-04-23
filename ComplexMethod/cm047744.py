def formatLang(
    env: Environment,
    value: float | typing.Literal[''],
    digits: int = 2,
    grouping: bool = True,
    dp: str | None = None,
    currency_obj: typing.Any | None = None,
    rounding_method: typing.Literal['HALF-UP', 'HALF-DOWN', 'HALF-EVEN', "UP", "DOWN"] = 'HALF-EVEN',
    rounding_unit: typing.Literal['decimals', 'units', 'thousands', 'lakhs', 'millions'] = 'decimals',
) -> str:
    """
    This function will format a number `value` to the appropriate format of the language used.

    :param env: The environment.
    :param value: The value to be formatted.
    :param digits: The number of decimals digits.
    :param grouping: Usage of language grouping or not.
    :param dp: Name of the decimals precision to be used. This will override ``digits``
                   and ``currency_obj`` precision.
    :param currency_obj: Currency to be used. This will override ``digits`` precision.
    :param rounding_method: The rounding method to be used:
        **'HALF-UP'** will round to the closest number with ties going away from zero,
        **'HALF-DOWN'** will round to the closest number with ties going towards zero,
        **'HALF_EVEN'** will round to the closest number with ties going to the closest
        even number,
        **'UP'** will always round away from 0,
        **'DOWN'** will always round towards 0.
    :param rounding_unit: The rounding unit to be used:
        **decimals** will round to decimals with ``digits`` or ``dp`` precision,
        **units** will round to units without any decimals,
        **thousands** will round to thousands without any decimals,
        **lakhs** will round to lakhs without any decimals,
        **millions** will round to millions without any decimals.

    :returns: The value formatted.
    """
    # We don't want to return 0
    if value == '':
        return ''

    if rounding_unit == 'decimals':
        if dp:
            digits = env['decimal.precision'].precision_get(dp)
        elif currency_obj:
            digits = currency_obj.decimal_places
    else:
        digits = 0

    rounding_unit_mapping = {
        'decimals': 1,
        'thousands': 10**3,
        'lakhs': 10**5,
        'millions': 10**6,
        'units': 1,
    }

    value /= rounding_unit_mapping[rounding_unit]

    rounded_value = float_round(value, precision_digits=digits, rounding_method=rounding_method)
    lang = env['res.lang'].browse(get_lang(env).id)
    formatted_value = lang.format(f'%.{digits}f', rounded_value, grouping=grouping)

    if currency_obj and currency_obj.symbol:
        arguments = (formatted_value, NON_BREAKING_SPACE, currency_obj.symbol)

        return '%s%s%s' % (arguments if currency_obj.position == 'after' else arguments[::-1])

    return formatted_value