def _read_blocks(self, base_block_id: str, page_last_edited_time: Optional[str] = None, page_path: Optional[str] = None) -> tuple[list[NotionBlock], list[str], list[Document]]:
        result_blocks: list[NotionBlock] = []
        child_pages: list[str] = []
        attachments: list[Document] = []
        cursor = None

        while True:
            data = self._fetch_child_blocks(base_block_id, cursor)

            if data is None:
                return result_blocks, child_pages, attachments

            for result in data["results"]:
                logging.debug(f"[Notion]: Found child block for block with ID {base_block_id}: {result}")
                result_block_id = result["id"]
                result_type = result["type"]
                result_obj = result[result_type]

                if result_type in ["ai_block", "unsupported", "external_object_instance_page"]:
                    logging.warning(f"[Notion]: Skipping unsupported block type {result_type}")
                    continue

                if result_type == "table":
                    table_html = self._build_table_html(result_block_id)
                    if table_html:
                        result_blocks.append(
                            NotionBlock(
                                id=result_block_id,
                                text=table_html,
                                prefix="\n\n",
                            )
                        )
                    continue

                if result_type == "equation":
                    expr = result_obj.get("expression")
                    if expr:
                        result_blocks.append(
                            NotionBlock(
                                id=result_block_id,
                                text=expr,
                                prefix="\n",
                            )
                        )
                    continue

                cur_result_text_arr = []
                if "rich_text" in result_obj:
                    text = self._extract_rich_text(result_obj["rich_text"])
                    if text:
                        cur_result_text_arr.append(text)

                if result_type == "bulleted_list_item":
                    if cur_result_text_arr:
                        cur_result_text_arr[0] = f"- {cur_result_text_arr[0]}"
                    else:
                        cur_result_text_arr = ["- "]

                if result_type == "numbered_list_item":
                    if cur_result_text_arr:
                        cur_result_text_arr[0] = f"1. {cur_result_text_arr[0]}"
                    else:
                        cur_result_text_arr = ["1. "]

                if result_type == "to_do":
                    checked = result_obj.get("checked")
                    checkbox_prefix = "[x]" if checked else "[ ]"
                    if cur_result_text_arr:
                        cur_result_text_arr = [f"{checkbox_prefix} {cur_result_text_arr[0]}"] + cur_result_text_arr[1:]
                    else:
                        cur_result_text_arr = [checkbox_prefix]

                if result_type in {"file", "image", "pdf", "video", "audio"}:
                    file_url, file_name, caption = self._extract_file_metadata(result_obj, result_block_id)
                    if file_url:
                        attachment_doc = self._build_attachment_document(
                            block_id=result_block_id,
                            url=file_url,
                            name=file_name,
                            caption=caption,
                            page_last_edited_time=page_last_edited_time,
                            page_path=page_path,
                        )
                        if attachment_doc:
                            attachments.append(attachment_doc)

                        attachment_label = file_name
                        if caption:
                            attachment_label = f"{file_name} ({caption})"
                        if attachment_label:
                            cur_result_text_arr.append(f"{result_type.capitalize()}: {attachment_label}")

                if result["has_children"]:
                    if result_type == "child_page":
                        child_pages.append(result_block_id)
                    else:
                        logging.debug(f"[Notion]: Entering sub-block: {result_block_id}")
                        subblocks, subblock_child_pages, subblock_attachments = self._read_blocks(result_block_id, page_last_edited_time, page_path)
                        logging.debug(f"[Notion]: Finished sub-block: {result_block_id}")
                        result_blocks.extend(subblocks)
                        child_pages.extend(subblock_child_pages)
                        attachments.extend(subblock_attachments)

                if result_type == "child_database":
                    inner_blocks, inner_child_pages = self._read_pages_from_database(result_block_id)
                    result_blocks.extend(inner_blocks)

                    if self.recursive_index_enabled:
                        child_pages.extend(inner_child_pages)

                if cur_result_text_arr:
                    new_block = NotionBlock(
                        id=result_block_id,
                        text="\n".join(cur_result_text_arr),
                        prefix="\n",
                    )
                    result_blocks.append(new_block)

            if data["next_cursor"] is None:
                break

            cursor = data["next_cursor"]

        return result_blocks, child_pages, attachments