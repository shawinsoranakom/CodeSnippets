def parse_token(token: str | float) -> float | str:
    if token in OPERATORS:
        return token
    try:
        return float(token)
    except ValueError:
        msg = f"{token} is neither a number nor a valid operator"
        raise ValueError(msg)
