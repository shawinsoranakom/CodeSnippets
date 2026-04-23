def filter_hint_type_list(hint_type_list: list[type]) -> list[type]:
        """Filter the hint type list."""
        new_hint_type_list = []
        primitive_types = {int, float, str, bool, list, dict, tuple, set}

        for hint_type in hint_type_list:
            # Skip primitive types and empty types
            # Check for _empty first (doesn't require hashing)
            if hint_type == _empty:
                continue

            # Skip Depends objects (they're not types we need to import)
            if (
                hasattr(hint_type, "__class__")
                and "Depends" in hint_type.__class__.__name__
            ):
                continue

            # Skip Annotated types that contain Depends in their metadata
            if isinstance(hint_type, _AnnotatedAlias):
                has_depends = False
                if hasattr(hint_type, "__metadata__"):
                    for meta in hint_type.__metadata__:
                        if (
                            hasattr(meta, "__class__")
                            and "Depends" in meta.__class__.__name__
                        ):
                            has_depends = True
                            break
                if has_depends:
                    continue

            # Now safe to check against primitive_types set
            try:
                if hint_type in primitive_types:
                    continue
            except TypeError:
                # If somehow we still get an unhashable type, skip it
                continue

            # Only include types that have a module and are not builtins
            if (
                hasattr(hint_type, "__module__") and hint_type.__module__ != "builtins"
            ) or (isinstance(hint_type, str)):
                new_hint_type_list.append(hint_type)

        # Deduplicate without using set() to handle unhashable types
        deduplicated: list = []
        for hint_type in new_hint_type_list:
            is_duplicate = False
            for existing in deduplicated:
                try:
                    if hint_type == existing:
                        is_duplicate = True
                        break
                except TypeError:
                    # If comparison fails, compare by identity
                    if id(hint_type) == id(existing):
                        is_duplicate = True
                        break

            if not is_duplicate:
                deduplicated.append(hint_type)

        return deduplicated