def get_secret_key(cls, value, info):
        config_dir = info.data.get("CONFIG_DIR")

        if not config_dir:
            logger.debug("No CONFIG_DIR provided, not saving secret key")
            return value or secrets.token_urlsafe(32)

        secret_key_path = Path(config_dir) / "secret_key"

        if value:
            logger.debug("Secret key provided")
            secret_value = value.get_secret_value() if isinstance(value, SecretStr) else value
            write_secret_to_file(secret_key_path, secret_value)
        elif secret_key_path.exists():
            value = read_secret_from_file(secret_key_path)
            logger.debug("Loaded secret key")
            if not value:
                value = secrets.token_urlsafe(32)
                write_secret_to_file(secret_key_path, value)
                logger.debug("Saved secret key")
        else:
            value = secrets.token_urlsafe(32)
            write_secret_to_file(secret_key_path, value)
            logger.debug("Saved secret key")

        return value if isinstance(value, SecretStr) else SecretStr(value).get_secret_value()