def round_away_from_one(value):
    return int(Decimal(value - 1).quantize(Decimal("0"), rounding=ROUND_UP)) + 1