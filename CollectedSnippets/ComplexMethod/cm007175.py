def _get_or_create_index(self, client: TwelveLabs) -> tuple[str, str]:
        """Get existing index or create new one.

        Returns (index_id, index_name).
        """
        # First check if index_id is provided and valid
        if hasattr(self, "index_id") and self.index_id:
            try:
                index = client.index.retrieve(id=self.index_id)
            except (ValueError, KeyError) as e:
                if not hasattr(self, "index_name") or not self.index_name:
                    error_msg = "Invalid index ID provided and no index name specified for fallback"
                    raise IndexCreationError(error_msg) from e
            else:
                return self.index_id, index.name

        # If index_name is provided, try to find it
        if hasattr(self, "index_name") and self.index_name:
            try:
                # List all indexes and find by name
                indexes = client.index.list()
                for idx in indexes:
                    if idx.name == self.index_name:
                        return idx.id, idx.name

                # If we get here, index wasn't found - create it
                index = client.index.create(
                    name=self.index_name,
                    models=[
                        {
                            "name": self.model_name if hasattr(self, "model_name") else "pegasus1.2",
                            "options": ["visual", "audio"],
                        }
                    ],
                )
            except (ValueError, KeyError) as e:
                error_msg = f"Error with index name {self.index_name}"
                raise IndexCreationError(error_msg) from e
            else:
                return index.id, index.name

        # If we get here, neither index_id nor index_name was provided
        error_msg = "Either index_name or index_id must be provided"
        raise IndexCreationError(error_msg)