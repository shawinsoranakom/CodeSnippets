def override_database_connection_timezone(timezone):
    try:
        orig_timezone = connection.settings_dict["TIME_ZONE"]
        connection.settings_dict["TIME_ZONE"] = timezone
        # Clear cached properties, after first accessing them to ensure they
        # exist.
        connection.timezone
        del connection.timezone
        connection.timezone_name
        del connection.timezone_name
        yield
    finally:
        connection.settings_dict["TIME_ZONE"] = orig_timezone
        # Clear cached properties, after first accessing them to ensure they
        # exist.
        connection.timezone
        del connection.timezone
        connection.timezone_name
        del connection.timezone_name