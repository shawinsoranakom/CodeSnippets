async def run(
        self,
        input_data: Input,
        *,
        credentials: OAuth2Credentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            entries, count, db_title = await self.query_database(
                credentials,
                input_data.database_id,
                input_data.filter_property,
                input_data.filter_value,
                input_data.sort_property,
                input_data.sort_direction or "ascending",
                input_data.limit,
            )
            # Yield the complete list for batch operations
            yield "entries", entries

            # Extract and yield IDs as a list for batch operations
            entry_ids = [entry["_id"] for entry in entries if "_id" in entry]
            yield "entry_ids", entry_ids

            # Yield each individual entry and its ID for single connections
            for entry in entries:
                yield "entry", entry
                if "_id" in entry:
                    yield "entry_id", entry["_id"]

            yield "count", count
            yield "database_title", db_title
        except Exception as e:
            yield "error", str(e) if str(e) else "Unknown error"