def _base10_to_85(d: int) -> str:
    return "".join(chr(d % 85 + 33)) + _base10_to_85(d // 85) if d > 0 else ""
