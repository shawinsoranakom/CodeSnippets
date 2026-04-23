def float_round(
    value: float,
    precision_digits: int | None = None,
    precision_rounding: float | None = None,
    rounding_method: RoundingMethod = 'HALF-UP',
) -> float:
    """Return ``value`` rounded to ``precision_digits`` decimal digits,
       minimizing IEEE-754 floating point representation errors, and applying
       the tie-breaking rule selected with ``rounding_method``, by default
       HALF-UP (away from zero).
       Precision must be given by ``precision_digits`` or ``precision_rounding``,
       not both!

       :param value: the value to round
       :param precision_digits: number of fractional digits to round to.
       :param precision_rounding: decimal number representing the minimum
           non-zero value at the desired precision (for example, 0.01 for a
           2-digit precision).
       :param rounding_method: the rounding method used:
           - 'HALF-UP' will round to the closest number with ties going away from zero.
           - 'HALF-DOWN' will round to the closest number with ties going towards zero.
           - 'HALF-EVEN' will round to the closest number with ties going to the closest
              even number.
           - 'UP' will always round away from 0.
           - 'DOWN' will always round towards 0.
       :return: rounded float
    """
    rounding_factor = _float_check_precision(precision_digits=precision_digits,
                                             precision_rounding=precision_rounding)
    if rounding_factor == 0 or value == 0:
        return 0.0

    # NORMALIZE - ROUND - DENORMALIZE
    # In order to easily support rounding to arbitrary 'steps' (e.g. coin values),
    # we normalize the value before rounding it as an integer, and de-normalize
    # after rounding: e.g. float_round(1.3, precision_rounding=.5) == 1.5
    def normalize(val):
        return val / rounding_factor

    def denormalize(val):
        return val * rounding_factor

    # inverting small rounding factors reduces rounding errors
    if rounding_factor < 1:
        rounding_factor = float_invert(rounding_factor)
        normalize, denormalize = denormalize, normalize

    normalized_value = normalize(value)

    # Due to IEEE-754 float/double representation limits, the approximation of the
    # real value may be slightly below the tie limit, resulting in an error of
    # 1 unit in the last place (ulp) after rounding.
    # For example 2.675 == 2.6749999999999998.
    # To correct this, we add a very small epsilon value, scaled to the
    # the order of magnitude of the value, to tip the tie-break in the right
    # direction.
    # Credit: discussion with OpenERP community members on bug 882036
    epsilon_magnitude = math.log2(abs(normalized_value))
    # `2**(epsilon_magnitude - 52)` would be the minimal size, but we increase it to be
    # more tolerant of inaccuracies accumulated after multiple floating point operations
    epsilon = 2**(epsilon_magnitude - 50)

    match rounding_method:
        case 'HALF-UP':  # 0.5 rounds away from 0
            result = round(normalized_value + math.copysign(epsilon, normalized_value))
        case 'HALF-EVEN':  # 0.5 rounds towards closest even number
            integral = math.floor(normalized_value)
            remainder = abs(normalized_value - integral)
            is_half = abs(0.5 - remainder) < epsilon
            # if is_half & integral is odd, add odd bit to make it even
            result = integral + (integral & 1) if is_half else round(normalized_value)
        case 'HALF-DOWN':  # 0.5 rounds towards 0
            result = round(normalized_value - math.copysign(epsilon, normalized_value))
        case 'UP':  # round to number furthest from zero
            result = math.trunc(normalized_value + math.copysign(1 - epsilon, normalized_value))
        case 'DOWN':  # round to number closest to zero
            result = math.trunc(normalized_value + math.copysign(epsilon, normalized_value))
        case _:
            msg = f"unknown rounding method: {rounding_method}"
            raise ValueError(msg)

    return denormalize(result)