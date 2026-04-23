async def __get_prices(call: ServiceCall) -> ServiceResponse:
    entries: list[TibberConfigEntry] = call.hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )
    tibber_connection = await entries[0].runtime_data.async_get_client(call.hass)

    start = __get_date(call.data.get(ATTR_START), "start")
    end = __get_date(call.data.get(ATTR_END), "end")

    if start >= end:
        end = start + dt.timedelta(days=1)

    tibber_prices: dict[str, Any] = {}

    now = dt_util.now()
    today_start = dt_util.start_of_local_day(now)
    today_end = today_start + dt.timedelta(days=1)
    tomorrow_end = today_start + dt.timedelta(days=2)

    def _has_valid_prices(home: tibber.TibberHome) -> bool:
        """Return True if the home has valid prices."""
        for price_start in home.price_total:
            start_dt = dt_util.as_local(datetime.fromisoformat(str(price_start)))

            if now.hour >= 13:
                if today_end <= start_dt < tomorrow_end:
                    return True
            elif today_start <= start_dt < today_end:
                return True
        return False

    for tibber_home in tibber_connection.get_homes(only_active=True):
        if not _has_valid_prices(tibber_home):
            try:
                await tibber_home.update_info_and_price_info()
            except TimeoutError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="get_prices_timeout",
                ) from err
            except tibber.InvalidLoginError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="get_prices_invalid_login",
                ) from err
            except (
                tibber.RetryableHttpExceptionError,
                tibber.FatalHttpExceptionError,
            ) as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="get_prices_communication_failed",
                    translation_placeholders={"detail": str(err.status)},
                ) from err
            except aiohttp.ClientError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="get_prices_communication_failed",
                    translation_placeholders={"detail": str(err)},
                ) from err
        home_nickname = tibber_home.name

        price_data = [
            {
                "start_time": starts_at,
                "price": price,
            }
            for starts_at, price in tibber_home.price_total.items()
        ]

        selected_data = [
            price
            for price in price_data
            if start <= dt.datetime.fromisoformat(str(price["start_time"])) < end
        ]
        tibber_prices[home_nickname] = selected_data

    return {"prices": tibber_prices}