def get_database_list_static(cls, token: str, environment: str | None = None):
        try:
            environment = cls.get_environment(environment)
            client = DataAPIClient(environment=environment)

            # Get the admin object
            admin_client = client.get_admin(token=token)

            # Get the list of databases
            db_list = admin_client.list_databases()

            # Generate the api endpoint for each database
            db_info_dict = {}
            for db in db_list:
                try:
                    # Get the API endpoint for the database
                    api_endpoints = [db_reg.api_endpoint for db_reg in db.regions]

                    # Get the number of collections
                    try:
                        # Get the number of collections in the database
                        num_collections = len(
                            client.get_database(
                                api_endpoints[0],
                                token=token,
                            ).list_collection_names()
                        )
                    except Exception:  # noqa: BLE001
                        if db.status != "PENDING":
                            continue
                        num_collections = 0

                    # Add the database to the dictionary
                    db_info_dict[db.name] = {
                        "api_endpoints": api_endpoints,
                        "keyspaces": db.keyspaces,
                        "collections": num_collections,
                        "status": db.status if db.status != "ACTIVE" else None,
                        "org_id": db.org_id if db.org_id else None,
                    }
                except Exception as e:  # noqa: BLE001
                    logger.debug("Failed to get metadata for database %s: %s", db.name, e)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error fetching database list: %s", e)
            return {}
        else:
            return db_info_dict