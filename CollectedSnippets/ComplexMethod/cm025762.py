async def _async_get_products(tesla: TeslaFleetApi) -> list[dict]:
    """Get products from Tesla Fleet API with region fallback handling."""
    try:
        return (await tesla.products())["response"]
    except InvalidRegion:
        LOGGER.warning("Region is invalid, trying to find the correct region")
    except (
        InvalidToken,
        OAuthExpired,
        LoginRequired,
        OAuth2TokenRequestReauthError,
    ) as e:
        raise ConfigEntryAuthFailed from e
    except (TeslaFleetError, OAuth2TokenRequestError) as e:
        raise ConfigEntryNotReady from e

    try:
        await tesla.find_server()
    except (
        InvalidToken,
        OAuthExpired,
        LoginRequired,
        LibraryError,
        OAuth2TokenRequestReauthError,
    ) as e:
        raise ConfigEntryAuthFailed from e
    except (TeslaFleetError, OAuth2TokenRequestError) as e:
        raise ConfigEntryNotReady from e

    try:
        return (await tesla.products())["response"]
    except (
        InvalidToken,
        OAuthExpired,
        LoginRequired,
        OAuth2TokenRequestReauthError,
    ) as e:
        raise ConfigEntryAuthFailed from e
    except (TeslaFleetError, OAuth2TokenRequestError) as e:
        raise ConfigEntryNotReady from e