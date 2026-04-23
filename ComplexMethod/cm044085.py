def merge_lists(base_list: list, update_list: list) -> list:
        """Merge two lists."""
        new_list: list = []
        update_items: dict = {}

        # Handle nested structures in lists
        for item in update_list:
            if isinstance(item, dict):
                for match_key in match_keys:
                    if match_key in item:
                        update_items[item[match_key]] = item
                        break
            elif isinstance(item, (list, dict)):
                new_list.append(item)

        for base_item in base_list:
            if isinstance(base_item, dict):
                matched = False
                for match_key in match_keys:
                    if match_key in base_item:
                        item_id = base_item[match_key]
                        if item_id in update_items:
                            merged = base_item.copy()
                            update_item = update_items.pop(item_id)
                            for k, v in update_item.items():
                                merged[k] = merge_values(merged.get(k), v)
                            new_list.append(merged)
                            matched = True
                            break
                if not matched:
                    new_list.append(base_item)
            elif isinstance(base_item, list):
                matching_update = next(
                    (x for x in update_list if isinstance(x, list)), None
                )
                if matching_update:
                    new_list.append(merge_lists(base_item, matching_update))
                else:
                    new_list.append(base_item)
            else:
                new_list.append(base_item)

        new_list.extend(update_items.values())

        return new_list