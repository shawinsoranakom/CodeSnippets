def batch_update_metadata(cls, kb_id: str, doc_ids: List[str], updates=None, deletes=None) -> int:
        """
        Batch update metadata for documents in a knowledge base.

        Args:
            kb_id: Knowledge base ID
            doc_ids: List of document IDs to update
            updates: List of update operations, each with:
                - key: field name to update
                - value: new value
                - match (optional): only update if current value matches this
            deletes: List of delete operations, each with:
                - key: field name to delete from
                - value (optional): specific value to delete (if not provided, deletes the entire field)

        Returns:
            Number of documents updated

        Examples:
            updates = [{"key": "author", "value": "John"}]
            updates = [{"key": "tags", "value": "new", "match": "old"}]  # Replace "old" with "new" in tags list
            deletes = [{"key": "author"}]  # Delete entire author field
            deletes = [{"key": "tags", "value": "obsolete"}]  # Remove "obsolete" from tags list
        """
        updates = updates or []
        deletes = deletes or []
        if not doc_ids:
            return 0

        def _normalize_meta(meta):
            """Normalize metadata to a dict."""
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    return {}
            if not isinstance(meta, dict):
                return {}
            return deepcopy(meta)

        def _str_equal(a, b):
            """Compare two values as strings."""
            return str(a) == str(b)

        def _apply_updates(meta):
            """Apply update operations to metadata."""
            changed = False
            for upd in updates:
                key = upd.get("key")
                if not key:
                    continue

                new_value = upd.get("value")
                match_value = upd.get("match", None)
                match_provided = match_value is not None and match_value != ""

                if key not in meta:
                    if match_provided:
                        continue
                    meta[key] = dedupe_list(new_value) if isinstance(new_value, list) else new_value
                    changed = True
                    continue

                if isinstance(meta[key], list):
                    if not match_provided:
                        # No match provided, append new_value to the list
                        if isinstance(new_value, list):
                            meta[key] = dedupe_list(meta[key] + new_value)
                        else:
                            meta[key] = dedupe_list(meta[key] + [new_value])
                        changed = True
                    else:
                        # Replace items matching match_value with new_value
                        replaced = False
                        new_list = []
                        for item in meta[key]:
                            if _str_equal(item, match_value):
                                new_list.append(new_value)
                                replaced = True
                            else:
                                new_list.append(item)
                        if replaced:
                            meta[key] = dedupe_list(new_list)
                            changed = True
                else:
                    if not match_provided:
                        meta[key] = new_value
                        changed = True
                    else:
                        if _str_equal(meta[key], match_value):
                            meta[key] = new_value
                            changed = True
            return changed

        def _apply_deletes(meta):
            """Apply delete operations to metadata."""
            changed = False
            for d in deletes:
                key = d.get("key")
                if not key or key not in meta:
                    continue
                value = d.get("value", None)
                if isinstance(meta[key], list):
                    if value is None:
                        del meta[key]
                        changed = True
                        continue
                    new_list = [item for item in meta[key] if not _str_equal(item, value)]
                    if len(new_list) != len(meta[key]):
                        if new_list:
                            meta[key] = new_list
                        else:
                            del meta[key]
                        changed = True
                else:
                    if value is None or _str_equal(meta[key], value):
                        del meta[key]
                        changed = True
            return changed

        try:
            results = cls._search_metadata(kb_id, condition={"kb_id": kb_id, "id": doc_ids})
            if not results:
                results = []  # Treat as empty list if None

            updated_docs = 0
            found_doc_ids = set()

            logging.debug(f"[batch_update_metadata] Searching for doc_ids: {doc_ids}")

            # Use helper to iterate over results
            for doc_id, doc in cls._iter_search_results(results):
                found_doc_ids.add(doc_id)

                # Get current metadata
                current_meta = cls._extract_metadata(doc)
                meta = _normalize_meta(current_meta)
                original_meta = deepcopy(meta)

                logging.debug(f"[batch_update_metadata] Doc {doc_id}: current_meta={current_meta}, meta={meta}")
                logging.debug(f"[batch_update_metadata] Updates to apply: {updates}, Deletes: {deletes}")

                # Apply updates and deletes
                changed = _apply_updates(meta)
                logging.debug(f"[batch_update_metadata] After _apply_updates: changed={changed}, meta={meta}")
                changed = _apply_deletes(meta) or changed
                logging.debug(f"[batch_update_metadata] After _apply_deletes: changed={changed}, meta={meta}")

                # Update if changed
                if changed and meta != original_meta:
                    logging.debug(f"[batch_update_metadata] Updating doc_id: {doc_id}, meta: {meta}")
                    # If metadata is empty, delete the row entirely instead of keeping empty metadata
                    if not meta:
                        cls.delete_document_metadata(doc_id, kb_id, tenant_id=None)
                    else:
                        cls.update_document_metadata(doc_id, meta)
                    updated_docs += 1

            # Handle documents that don't have metadata rows yet
            # These documents weren't in the search results, so we need to insert new metadata for them
            doc_ids_set = set(doc_ids)
            missing_doc_ids = doc_ids_set - found_doc_ids
            if missing_doc_ids and updates:
                logging.debug(f"[batch_update_metadata] Inserting new metadata for documents without metadata rows: {missing_doc_ids}")
                for doc_id in missing_doc_ids:
                    # Apply updates to create new metadata
                    meta = {}
                    _apply_updates(meta)
                    if meta:
                        # Only insert if there's actual metadata to add
                        cls.update_document_metadata(doc_id, meta)
                        updated_docs += 1
                        logging.debug(f"[batch_update_metadata] Inserted metadata for doc_id: {doc_id}, meta: {meta}")

            logging.debug(f"[batch_update_metadata] KB: {kb_id}, doc_ids: {doc_ids}, updated: {updated_docs}")
            return updated_docs

        except Exception as e:
            logging.error(f"Error in batch_update_metadata for KB {kb_id}: {e}")
            return 0