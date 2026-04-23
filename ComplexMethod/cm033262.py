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