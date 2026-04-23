async def get_blocks(self, block_id: str, recursive: bool = True) -> List[dict]:
        """
        Fetch all blocks from a page or block.

        Args:
            block_id: The ID of the page or block to fetch children from.
            recursive: Whether to fetch nested blocks recursively.

        Returns:
            List of block objects.
        """
        blocks = []
        cursor = None

        while True:
            url = f"https://api.notion.com/v1/blocks/{block_id}/children"
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor

            response = await self.requests.get(url, headers=self.headers, params=params)

            if not response.ok:
                raise NotionAPIException(
                    f"Failed to fetch blocks: {response.status} - {response.text()}",
                    response.status,
                )

            data = response.json()
            current_blocks = data.get("results", [])

            # If recursive, fetch children for blocks that have them
            if recursive:
                for block in current_blocks:
                    if block.get("has_children"):
                        block["children"] = await self.get_blocks(
                            block["id"], recursive=True
                        )

            blocks.extend(current_blocks)

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

        return blocks