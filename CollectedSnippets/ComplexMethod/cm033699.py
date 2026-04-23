def get_config(config_path: str) -> dict[str, str]:
    """Return a configuration dictionary parsed from the given configuration path."""
    parser = configparser.ConfigParser()
    parser.read(config_path)

    config = dict((key.upper(), value) for key, value in parser.items('default'))

    rg_vars = (
        'RESOURCE_GROUP',
        'RESOURCE_GROUP_SECONDARY',
    )

    sp_vars = (
        'AZURE_CLIENT_ID',
        'AZURE_SECRET',
        'AZURE_SUBSCRIPTION_ID',
        'AZURE_TENANT',
    )

    ad_vars = (
        'AZURE_AD_USER',
        'AZURE_PASSWORD',
        'AZURE_SUBSCRIPTION_ID',
    )

    rg_ok = all(var in config for var in rg_vars)
    sp_ok = all(var in config for var in sp_vars)
    ad_ok = all(var in config for var in ad_vars)

    if not rg_ok:
        raise ApplicationError('Resource groups must be defined with: %s' % ', '.join(sorted(rg_vars)))

    if not sp_ok and not ad_ok:
        raise ApplicationError('Credentials must be defined using either:\nService Principal: %s\nActive Directory: %s' % (
            ', '.join(sorted(sp_vars)), ', '.join(sorted(ad_vars))))

    return config