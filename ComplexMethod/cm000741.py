async def search_workspace(
        credentials: OAuth2Credentials,
        query: str = "",
        filter_type: Optional[str] = None,
        limit: int = 20,
    ) -> tuple[List[NotionSearchResult], int]:
        """
        Search the Notion workspace.

        Returns:
            Tuple of (results_list, count)
        """
        client = NotionClient(credentials)

        # Build filter if type is specified
        filter_obj = None
        if filter_type:
            filter_obj = {"property": "object", "value": filter_type}

        # Execute search
        response = await client.search(
            query=query, filter_obj=filter_obj, page_size=limit
        )

        # Parse results
        results = []
        for item in response.get("results", []):
            result_data = {
                "id": item.get("id", ""),
                "type": item.get("object", ""),
                "url": item.get("url", ""),
                "created_time": item.get("created_time"),
                "last_edited_time": item.get("last_edited_time"),
                "title": "",  # Will be set below
            }

            # Extract title based on type
            if item.get("object") == "page":
                # For pages, get the title from properties
                result_data["title"] = extract_page_title(item)

                # Add parent info
                parent = item.get("parent", {})
                if parent.get("type") == "page_id":
                    result_data["parent_type"] = "page"
                    result_data["parent_id"] = parent.get("page_id")
                elif parent.get("type") == "database_id":
                    result_data["parent_type"] = "database"
                    result_data["parent_id"] = parent.get("database_id")
                elif parent.get("type") == "workspace":
                    result_data["parent_type"] = "workspace"

                # Add icon if present
                icon = item.get("icon")
                if icon and icon.get("type") == "emoji":
                    result_data["icon"] = icon.get("emoji")

            elif item.get("object") == "database":
                # For databases, get title from the title array
                result_data["title"] = parse_rich_text(item.get("title", []))

                # Add database-specific metadata
                result_data["is_inline"] = item.get("is_inline", False)

                # Add parent info
                parent = item.get("parent", {})
                if parent.get("type") == "page_id":
                    result_data["parent_type"] = "page"
                    result_data["parent_id"] = parent.get("page_id")
                elif parent.get("type") == "workspace":
                    result_data["parent_type"] = "workspace"

                # Add icon if present
                icon = item.get("icon")
                if icon and icon.get("type") == "emoji":
                    result_data["icon"] = icon.get("emoji")

            results.append(NotionSearchResult(**result_data))

        return results, len(results)