async def get_options_symbols(symbol: OptionsSymbols = "BTC") -> dict:
    """
    Get a dictionary of contract symbols by expiry.

    Parameters
    ----------
    symbol : OptionsSymbols
        The underlying symbol to get options for. Default is "btc".

    Returns
    -------
    dict[str, str]
        A dictionary of contract symbols by expiry date.
    """
    # pylint: disable=import-outside-toplevel
    from pandas import to_datetime

    if symbol.upper() not in DERIBIT_OPTIONS_SYMBOLS:
        raise ValueError(
            f"Invalid Deribit symbol. Supported symbols are: {', '.join(DERIBIT_OPTIONS_SYMBOLS)}",
        )

    currency = (
        "USDC" if symbol.upper() in ["BNB", "PAXG", "SOL", "XRP"] else symbol.upper()
    )
    instruments = await get_instruments(currency, "option")
    expirations: dict = {}
    all_options = list(
        set(
            d.get("instrument_name")
            for d in instruments
            if d.get("instrument_name").startswith(symbol)
            and d.get("instrument_name").endswith(("-C", "-P"))
        )
    )
    for item in sorted(
        list(
            set(
                (
                    to_datetime(d.split("-")[1]).date().strftime("%Y-%m-%d"),
                    d.split("-")[1],
                )
                for d in all_options
            )
        )
    ):
        expirations[item[0]] = item[1]

    return {k: [d for d in all_options if v in d] for k, v in expirations.items()}