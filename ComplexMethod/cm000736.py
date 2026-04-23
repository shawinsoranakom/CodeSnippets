async def query_database(
        credentials: OAuth2Credentials,
        database_id: str,
        filter_property: Optional[str] = None,
        filter_value: Optional[str] = None,
        sort_property: Optional[str] = None,
        sort_direction: str = "ascending",
        limit: int = 100,
    ) -> tuple[List[Dict[str, Any]], int, str]:
        """
        Query a Notion database and parse the results.

        Returns:
            Tuple of (entries_list, count, database_title)
        """
        client = NotionClient(credentials)

        # Build filter if specified
        filter_obj = None
        if filter_property and filter_value:
            filter_obj = NotionReadDatabaseBlock._build_filter(
                filter_property, filter_value
            )

        # Build sorts if specified
        sorts = None
        if sort_property:
            sorts = [{"property": sort_property, "direction": sort_direction}]

        # Query the database
        result = await client.query_database(
            database_id, filter_obj=filter_obj, sorts=sorts, page_size=limit
        )

        # Parse the entries
        entries = []
        for page in result.get("results", []):
            entry = {}
            properties = page.get("properties", {})

            for prop_name, prop_value in properties.items():
                entry[prop_name] = NotionReadDatabaseBlock._parse_property_value(
                    prop_value
                )

            # Add metadata
            entry["_id"] = page.get("id")
            entry["_url"] = page.get("url")
            entry["_created_time"] = page.get("created_time")
            entry["_last_edited_time"] = page.get("last_edited_time")

            entries.append(entry)

        # Get database title (we need to make a separate call for this)
        try:
            database_url = f"https://api.notion.com/v1/databases/{database_id}"
            db_response = await client.requests.get(
                database_url, headers=client.headers
            )
            if db_response.ok:
                db_data = db_response.json()
                db_title = parse_rich_text(db_data.get("title", []))
            else:
                db_title = "Unknown Database"
        except Exception:
            db_title = "Unknown Database"

        return entries, len(entries), db_title