def get_api_endpoint_static(
        cls,
        token: str,
        environment: str | None = None,
        api_endpoint: str | None = None,
        database_name: str | None = None,
    ):
        # If the api_endpoint is set, return it
        if api_endpoint:
            return api_endpoint

        # Check if the database_name is like a url
        if database_name and database_name.startswith("https://"):
            return database_name

        # If the database is not set, nothing we can do.
        if not database_name:
            return None

        # Grab the database object
        environment = cls.get_environment(environment)
        db = cls.get_database_list_static(token=token, environment=environment).get(database_name)
        if not db:
            return None

        # Otherwise, get the URL from the database list
        endpoints = db.get("api_endpoints") or []
        return endpoints[0] if endpoints else None