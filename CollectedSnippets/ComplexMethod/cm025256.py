def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensors.

    Login to the bank and get a list of existing accounts. Create a
    sensor for each account.
    """
    credentials = BankCredentials(
        config[CONF_BIN], config[CONF_USERNAME], config[CONF_PIN], config[CONF_URL]
    )
    fints_name = cast(str, config.get(CONF_NAME, config[CONF_BIN]))

    account_config = {
        acc[CONF_ACCOUNT]: acc[CONF_NAME] for acc in config[CONF_ACCOUNTS]
    }

    holdings_config = {
        acc[CONF_ACCOUNT]: acc[CONF_NAME] for acc in config[CONF_HOLDINGS]
    }

    client = FinTsClient(credentials, fints_name, account_config, holdings_config)
    balance_accounts, holdings_accounts = client.detect_accounts()
    accounts: list[SensorEntity] = []

    for account in balance_accounts:
        if config[CONF_ACCOUNTS] and account.iban not in account_config:
            _LOGGER.debug("Skipping account %s for bank %s", account.iban, fints_name)
            continue

        if not (account_name := account_config.get(account.iban)):
            account_name = f"{fints_name} - {account.iban}"
        accounts.append(FinTsAccount(client, account, account_name))
        _LOGGER.debug("Creating account %s for bank %s", account.iban, fints_name)

    for account in holdings_accounts:
        if config[CONF_HOLDINGS] and account.accountnumber not in holdings_config:
            _LOGGER.debug(
                "Skipping holdings %s for bank %s", account.accountnumber, fints_name
            )
            continue

        account_name = holdings_config.get(account.accountnumber)
        if not account_name:
            account_name = f"{fints_name} - {account.accountnumber}"
        accounts.append(FinTsHoldingsAccount(client, account, account_name))
        _LOGGER.debug(
            "Creating holdings %s for bank %s", account.accountnumber, fints_name
        )

    add_entities(accounts, True)