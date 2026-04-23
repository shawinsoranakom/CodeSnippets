async def create_page(
        credentials: OAuth2Credentials,
        title: str,
        parent_page_id: Optional[str] = None,
        parent_database_id: Optional[str] = None,
        content: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        icon_emoji: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Create a new Notion page.

        Returns:
            Tuple of (page_id, page_url)
        """
        if not parent_page_id and not parent_database_id:
            raise ValueError(
                "Either parent_page_id or parent_database_id must be provided"
            )
        if parent_page_id and parent_database_id:
            raise ValueError(
                "Only one of parent_page_id or parent_database_id should be provided, not both"
            )

        client = NotionClient(credentials)

        # Build parent object
        if parent_page_id:
            parent = {"type": "page_id", "page_id": parent_page_id}
        else:
            parent = {"type": "database_id", "database_id": parent_database_id}

        # Build properties
        page_properties = NotionCreatePageBlock._build_properties(title, properties)

        # Convert content to blocks if provided
        children = None
        if content:
            children = NotionCreatePageBlock._markdown_to_blocks(content)

        # Build icon if provided
        icon = None
        if icon_emoji:
            icon = {"type": "emoji", "emoji": icon_emoji}

        # Create the page
        result = await client.create_page(
            parent=parent, properties=page_properties, children=children, icon=icon
        )

        page_id = result.get("id", "")
        page_url = result.get("url", "")

        if not page_id or not page_url:
            raise ValueError("Failed to get page ID or URL from Notion response")

        return page_id, page_url