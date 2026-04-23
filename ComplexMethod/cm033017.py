def _read_pages_from_database(self, database_id: str) -> tuple[list[NotionBlock], list[str]]:
        """Returns a list of top level blocks and all page IDs in the database."""
        result_blocks: list[NotionBlock] = []
        result_pages: list[str] = []
        cursor = None

        while True:
            data = self._fetch_database(database_id, cursor)

            for result in data["results"]:
                obj_id = result["id"]
                obj_type = result["object"]
                text = properties_to_str(result.get("properties", {}))

                if text:
                    result_blocks.append(NotionBlock(id=obj_id, text=text, prefix="\n"))

                if self.recursive_index_enabled:
                    if obj_type == "page":
                        logging.debug(f"[Notion]: Found page with ID {obj_id} in database {database_id}")
                        result_pages.append(result["id"])
                    elif obj_type == "database":
                        logging.debug(f"[Notion]: Found database with ID {obj_id} in database {database_id}")
                        _, child_pages = self._read_pages_from_database(obj_id)
                        result_pages.extend(child_pages)

            if data["next_cursor"] is None:
                break

            cursor = data["next_cursor"]

        return result_blocks, result_pages