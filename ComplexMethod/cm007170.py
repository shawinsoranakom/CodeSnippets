def _get_or_create_index(self, client: TwelveLabs) -> tuple[str, str]:
        """Get existing index or create new one.

        Returns (index_id, index_name).
        """
        # First check if index_id is provided and valid
        if hasattr(self, "_index_id") and self._index_id:
            try:
                index = client.index.retrieve(id=self._index_id)
                self.log(f"Found existing index with ID: {self._index_id}")
            except (ValueError, KeyError) as e:
                self.log(f"Error retrieving index with ID {self._index_id}: {e!s}", "WARNING")
            else:
                return self._index_id, index.name

        # If index_name is provided, try to find it
        if hasattr(self, "_index_name") and self._index_name:
            try:
                # List all indexes and find by name
                indexes = client.index.list()
                for idx in indexes:
                    if idx.name == self._index_name:
                        self.log(f"Found existing index: {self._index_name} (ID: {idx.id})")
                        return idx.id, idx.name

                # If we get here, index wasn't found - create it
                self.log(f"Creating new index: {self._index_name}")
                index = client.index.create(
                    name=self._index_name,
                    models=[
                        {
                            "name": self.model_name if hasattr(self, "model_name") else "pegasus1.2",
                            "options": ["visual", "audio"],
                        }
                    ],
                )
            except (ValueError, KeyError) as e:
                self.log(f"Error with index name {self._index_name}: {e!s}", "ERROR")
                error_message = f"Error with index name {self._index_name}"
                raise IndexCreationError(error_message) from e
            else:
                return index.id, index.name

        # If neither is provided, create a new index with timestamp
        try:
            index_name = f"index_{int(time.time())}"
            self.log(f"Creating new index: {index_name}")
            index = client.index.create(
                name=index_name,
                models=[
                    {
                        "name": self.model_name if hasattr(self, "model_name") else "pegasus1.2",
                        "options": ["visual", "audio"],
                    }
                ],
            )
        except (ValueError, KeyError) as e:
            self.log(f"Failed to create new index: {e!s}", "ERROR")
            error_message = "Failed to create new index"
            raise IndexCreationError(error_message) from e
        else:
            return index.id, index.name