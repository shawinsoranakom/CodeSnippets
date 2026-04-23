def validate_symbols(cls, v):
        """Validate each symbol to check if it is a valid indicator."""
        # pylint: disable=import-outside-toplevel
        from openbb_econdb.utils import helpers

        INDICATORS = list(helpers.INDICATORS_DESCRIPTIONS)
        if not v:
            v = "main"
        symbols = v if isinstance(v, list) else v.split(",")
        new_symbols: list[str] = []
        for symbol in symbols:
            if "_" in symbol:
                new_symbols.append(symbol)
                continue
            if symbol.upper() == "MAIN":
                if len(symbols) > 1:
                    raise OpenBBError(
                        "The 'main' indicator cannot be combined with other indicators."
                    )
                return symbol
            if not any(
                (
                    symbol.upper().startswith(indicator)
                    if len(symbol) >= len(indicator)
                    else symbol.upper() == indicator
                )
                for indicator in INDICATORS
            ):
                warn(f"Invalid indicator: '{symbol}'.")
            else:
                new_symbols.append(symbol)
        if not new_symbols:
            raise OpenBBError(
                "No valid indicators provided. Please choose from: "
                + ",".join(INDICATORS)
            )
        return ",".join(new_symbols)