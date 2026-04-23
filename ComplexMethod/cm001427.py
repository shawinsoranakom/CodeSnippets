async def search_blocks(self, query: str) -> str:
        """Search blocks via platform API.

        Args:
            query: Search query for finding blocks.

        Returns:
            JSON string with search results.
        """
        try:
            blocks = await self._get_blocks()
            query_lower = query.lower()
            results: list[dict[str, Any]] = []

            for block in blocks:
                name = block.get("name", "")
                description = block.get("description", "")
                categories = [
                    c.get("category", "") for c in block.get("categories", [])
                ]

                # Check for match
                name_match = query_lower in name.lower()
                desc_match = query_lower in description.lower()
                cat_match = any(query_lower in c.lower() for c in categories)

                if name_match or desc_match or cat_match:
                    results.append(
                        {
                            "id": block.get("id"),
                            "name": name,
                            "description": description,
                            "categories": categories,
                            "input_schema": block.get("inputSchema", {}),
                        }
                    )

                    if len(results) >= 20:
                        break

            return json.dumps(
                {
                    "count": len(results),
                    "blocks": results,
                    "hint": "Use execute_block with the block 'id' to run a block",
                },
                indent=2,
            )
        except Exception as e:
            logger.error(f"Error searching blocks: {e}")
            return json.dumps({"error": str(e)})