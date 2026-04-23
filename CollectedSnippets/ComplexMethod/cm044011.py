def parse_symbols(
    symbol,
    transform: str | None = None,
    countries: str | list[str] | None = None,
):
    """Parse the indicator symbol with the optional transformation for a list of countries. Returns a string list."""
    symbols = []
    if not countries:
        if transform:
            symbol += "~" + transform
        symbols.append(symbol)
    elif countries and HAS_COUNTRIES.get(symbol, False) is False:
        raise OpenBBError(f"Indicator {symbol} does not have countries.")
    elif countries and HAS_COUNTRIES.get(symbol, False) is True:
        countries = countries if isinstance(countries, list) else countries.split(",")
        for country in countries:
            new_country = (
                "EA19"
                if country == "EA" and (symbol in ["URATE", "POP", "GDEBT"])
                else country
            )
            new_symbol = symbol + new_country
            if transform:
                new_symbol += "~" + transform
            symbols.append(new_symbol)

    return ",".join(symbols)