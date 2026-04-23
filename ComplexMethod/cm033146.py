def merge_block_text(cls, parser_result):
        block_content = []
        current_content = ""
        table_info_list = []
        last_block_id = None
        for item in parser_result:
            content = item.get("content")
            tag_name = item.get("tag_name")
            title_flag = tag_name in TITLE_TAGS
            block_id = item.get("metadata", {}).get("block_id")
            if block_id:
                if title_flag:
                    content = f"{TITLE_TAGS[tag_name]} {content}"
                if last_block_id != block_id:
                    if last_block_id is not None:
                        block_content.append(current_content)
                    current_content = content
                    last_block_id = block_id
                else:
                    current_content += (" " if current_content else "") + content
            else:
                if tag_name == "table":
                    table_info_list.append(item)
                else:
                    current_content += (" " if current_content else "") + content
        if current_content:
            block_content.append(current_content)
        return block_content, table_info_list