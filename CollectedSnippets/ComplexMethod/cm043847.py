async def get_instruments(
    currency: Currencies = "BTC",
    derivative_type: DerivativeTypes | None = None,
    expired: bool = False,
) -> list[dict]:
    """
    Get Deribit instruments.

    Parameters
    ----------
    currency : Currencies
        The currency to get instruments for. Default is "BTC".
    derivative_type : Optional[DerivativeTypes]
        The type of derivative to get instruments for. Default is None, which gets all types.

    Returns
    -------
    list[dict]
        A list of instrument dictionaries.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import amake_request

    if currency != "all" and currency.upper() not in CURRENCIES:
        raise ValueError(
            f"Currency {currency} not supported. Supported currencies are: {', '.join(CURRENCIES)}"
        )
    if derivative_type and derivative_type not in DERIVATIVE_TYPES:
        raise ValueError(
            f"Kind {derivative_type} not supported. Supported kinds are: {', '.join(DERIVATIVE_TYPES)}"
        )

    url = f"{BASE_URL}/api/v2/public/get_instruments?currency={currency.upper() if currency != 'all' else 'any'}"

    if derivative_type is not None:
        url += f"&kind={derivative_type}"

    if expired:
        url += f"&expired={str(expired).lower()}"

    try:
        response = await amake_request(url)
        return response.get("result", [])  # type: ignore
    except Exception as e:  # pylint: disable=broad-except
        raise OpenBBError(
            f"Failed to get instruments -> {e.__class__.__name__}: {e}"
        ) from e