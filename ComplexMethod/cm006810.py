def _initialize_collection_options(self, api_endpoint: str | None = None):
        # Nothing to generate if we don't have an API endpoint yet
        api_endpoint = api_endpoint or self.get_api_endpoint()
        if not api_endpoint:
            return []

        # Retrieve the database object
        database = self.get_database_object(api_endpoint=api_endpoint)

        # Get the list of collections
        collection_list = database.list_collections(keyspace=self.get_keyspace())

        # Return the list of collections and metadata associated
        return [
            {
                "name": col.name,
                "records": self.collection_data(collection_name=col.name, database=database),
                "provider": (
                    col.definition.vector.service.provider
                    if col.definition.vector and col.definition.vector.service
                    else None
                ),
                "icon": self.get_provider_icon(collection=col),
                "model": (
                    col.definition.vector.service.model_name
                    if col.definition.vector and col.definition.vector.service
                    else None
                ),
            }
            for col in collection_list
        ]