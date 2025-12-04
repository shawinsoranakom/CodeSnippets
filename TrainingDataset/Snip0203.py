def check_keys(key_a: int, key_b: int, mode: str) -> None:
    if mode == "encrypt":
        if key_a == 1:
            sys.exit(
                "The affine cipher becomes weak when key "
                "A is set to 1. Choose different key"
            )
        if key_b == 0:
            sys.exit(
                "The affine cipher becomes weak when key "
                "B is set to 0. Choose different key"
            )
    if key_a < 0 or key_b < 0 or key_b > len(SYMBOLS) - 1:
        sys.exit(
            "Key A must be greater than 0 and key B must "
            f"be between 0 and {len(SYMBOLS) - 1}."
        )
    if gcd_by_iterative(key_a, len(SYMBOLS)) != 1:
        sys.exit(
            f"Key A {key_a} and the symbol set size {len(SYMBOLS)} "
            "are not relatively prime. Choose a different key."
        )
