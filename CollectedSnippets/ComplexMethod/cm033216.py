def remove_chunks(self, items):
        # Handle two cases:
        # 1. REMOVE CHUNKS quoted_string (COMMA quoted_string)* FROM DOCUMENT quoted_string ";"
        # 2. REMOVE ALL CHUNKS FROM DOCUMENT quoted_string ";"

        # Check if it's "REMOVE ALL CHUNKS"
        for item in items:
            if hasattr(item, 'type') and item.type == 'ALL':
                # Find doc_id
                for j, inner_item in enumerate(items):
                    if hasattr(inner_item, 'type') and inner_item.type == 'DOCUMENT':
                        doc_id = items[j + 1].children[0].strip("'\"")
                        return {"type": "remove_chunks", "doc_id": doc_id, "delete_all": True}

        # Otherwise, we have chunk_ids
        chunk_ids = []
        doc_id = None
        for i, item in enumerate(items):
            if hasattr(item, 'type') and item.type == 'DOCUMENT':
                doc_id = items[i + 1].children[0].strip("'\"")
            elif hasattr(item, 'children') and item.children:
                val = item.children[0].strip("'\"")
                # Skip if it's "FROM" or "DOCUMENT"
                if val.upper() in ['FROM', 'DOCUMENT']:
                    continue
                chunk_ids.append(val)

        return {"type": "remove_chunks", "doc_id": doc_id, "chunk_ids": chunk_ids}