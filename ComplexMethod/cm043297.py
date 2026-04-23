async def _get(db):
            async with db.execute(
                "SELECT * FROM crawled_data WHERE url = ?", (url,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                # Get column names
                columns = [description[0] for description in cursor.description]
                # Create dict from row data
                row_dict = dict(zip(columns, row))

                # Load content from files using stored hashes
                content_fields = {
                    "html": row_dict["html"],
                    "cleaned_html": row_dict["cleaned_html"],
                    "markdown": row_dict["markdown"],
                    "extracted_content": row_dict["extracted_content"],
                    "screenshot": row_dict["screenshot"],
                    "screenshots": row_dict["screenshot"],
                }

                for field, hash_value in content_fields.items():
                    if hash_value:
                        content = await self._load_content(
                            hash_value,
                            field.split("_")[0],  # Get content type from field name
                        )
                        row_dict[field] = content or ""
                    else:
                        row_dict[field] = ""

                # Parse JSON fields
                json_fields = [
                    "media",
                    "links",
                    "metadata",
                    "response_headers",
                    "markdown",
                ]
                for field in json_fields:
                    try:
                        row_dict[field] = (
                            json.loads(row_dict[field]) if row_dict[field] else {}
                        )
                    except json.JSONDecodeError:
                        # Very UGLY, never mention it to me please
                        if field == "markdown" and isinstance(row_dict[field], str):
                            row_dict[field] = MarkdownGenerationResult(
                                raw_markdown=row_dict[field] or "",
                                markdown_with_citations="",
                                references_markdown="",
                                fit_markdown="",
                                fit_html="",
                            )
                        else:
                            row_dict[field] = {}

                if isinstance(row_dict["markdown"], Dict):
                    if row_dict["markdown"].get("raw_markdown"):
                        row_dict["markdown"] = row_dict["markdown"]["raw_markdown"]

                # Parse downloaded_files
                try:
                    row_dict["downloaded_files"] = (
                        json.loads(row_dict["downloaded_files"])
                        if row_dict["downloaded_files"]
                        else []
                    )
                except json.JSONDecodeError:
                    row_dict["downloaded_files"] = []

                # Remove any fields not in CrawlResult model
                valid_fields = CrawlResult.__annotations__.keys()
                filtered_dict = {k: v for k, v in row_dict.items() if k in valid_fields}
                filtered_dict["markdown"] = row_dict["markdown"]
                return CrawlResult(**filtered_dict)