def build(self, **kwargs: Any) -> None:  # noqa: ARG002 - Required for parent class compatibility
        """Process the Astra DB results and extract TwelveLabs index information."""
        if not self.astra_results:
            return

        # Convert to list if single item
        results = self.astra_results if isinstance(self.astra_results, list) else [self.astra_results]

        # Try to extract index information from metadata
        for doc in results:
            if not isinstance(doc, Data):
                continue

            # Get the metadata, handling the nested structure
            metadata = {}
            if hasattr(doc, "metadata") and isinstance(doc.metadata, dict):
                # Handle nested metadata using .get() method
                metadata = doc.metadata.get("metadata", doc.metadata)

            # Extract index_id and video_id
            self._index_id = metadata.get("index_id")
            self._video_id = metadata.get("video_id")

            # If we found both, we can stop searching
            if self._index_id and self._video_id:
                break