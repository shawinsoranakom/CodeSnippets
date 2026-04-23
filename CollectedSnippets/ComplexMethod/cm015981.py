def format_categories(ptr_pair: int):
            target_key = ptr_pair_to_key.get(ptr_pair)
            if target_key is None:
                return "???"

            matches = tuple(
                (version, category.name if category else "???")
                for (key, version), category in snapshot.items()
                if key == target_key
            )
            if not matches:
                raise AssertionError("Failed to lookup Tensor")

            # Deduplicate version bumps which don't change the category.
            categories = [matches[0][1]]
            for _, category in matches:
                if category != categories[-1]:
                    categories.append(category)

            return f"{target_key.storage.allocation_id} ({','.join(categories)})"