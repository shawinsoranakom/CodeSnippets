async def _convert_df_to_data_objects(
        self, df_source: pd.DataFrame, config_list: list[dict[str, Any]]
    ) -> list[Data]:
        """Convert DataFrame to Data objects for vector store."""
        data_objects: list[Data] = []

        # Set up vector store directory
        kb_path = await self._kb_path()

        # If we don't allow duplicates, we need to get the existing hashes
        chroma = Chroma(
            persist_directory=str(kb_path),
            collection_name=self.knowledge_base,
        )

        # Get all documents and their metadata
        all_docs = chroma.get()

        # Extract all _id values from metadata
        id_list = [metadata.get("_id") for metadata in all_docs["metadatas"] if metadata.get("_id")]

        # Get column roles
        content_cols = []
        identifier_cols = []

        for config in config_list:
            col_name = config.get("column_name")
            vectorize = config.get("vectorize") == "True" or config.get("vectorize") is True
            identifier = config.get("identifier") == "True" or config.get("identifier") is True

            if vectorize:
                content_cols.append(col_name)
            elif identifier:
                identifier_cols.append(col_name)

        # Convert each row to a Data object
        for _, row in df_source.iterrows():
            # Build content text from identifier columns using list comprehension
            identifier_parts = [str(row[col]) for col in content_cols if col in row and self._scalar_notna(row[col])]

            # Join all parts into a single string
            page_content = " ".join(identifier_parts)

            # Build metadata from NON-vectorized columns only (simple key-value pairs)
            data_dict = {
                "text": page_content,  # Main content for vectorization
            }

            # Add identifier columns if they exist
            if identifier_cols:
                identifier_parts = [
                    str(row[col]) for col in identifier_cols if col in row and self._scalar_notna(row[col])
                ]
                page_content = " ".join(identifier_parts)

            # Add metadata columns as simple key-value pairs
            for col in df_source.columns:
                if col not in content_cols and col in row and self._scalar_notna(row[col]):
                    # Convert to simple types for Chroma metadata
                    value = row[col]
                    data_dict[col] = str(value)  # Convert complex types to string

            # Hash the page_content for unique ID
            page_content_hash = hashlib.sha256(page_content.encode()).hexdigest()
            data_dict["_id"] = page_content_hash

            # If duplicates are disallowed, and hash exists, prevent adding this row
            if not self.allow_duplicates and page_content_hash in id_list:
                self.log(f"Skipping duplicate row with hash {page_content_hash}")
                continue

            # Create Data object - everything except "text" becomes metadata
            data_obj = Data(data=data_dict)
            data_objects.append(data_obj)

        return data_objects