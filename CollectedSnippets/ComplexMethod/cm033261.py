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