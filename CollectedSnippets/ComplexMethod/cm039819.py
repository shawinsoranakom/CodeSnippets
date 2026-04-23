def _check_consistency_items(
    items_docs,
    type_or_desc,
    section,
    n_objects,
    descr_regex_pattern="",
    ignore_types=tuple(),
):
    """Helper to check docstring consistency of all `items_docs`.

    If item is not present in all objects, checking is skipped and warning raised.
    If `regex` provided, match descriptions to all descriptions.

    Parameters
    ----------
    items_doc : dict of dict of str
        Dictionary where the key is the string type or description, value is
        a dictionary where the key is "type description" or "description"
        and the value is a list of object names with the same string type or
        description.

    type_or_desc : {"type description", "description"}
        Whether to check type description or description between objects.

    section : {"Parameters", "Attributes", "Returns"}
        Name of the section type.

    n_objects : int
        Total number of objects.

    descr_regex_pattern : str, default=""
        Regex pattern to match for description of all objects.
        Ignored when `type_or_desc="type description".

    ignore_types : tuple of str, default=()
        Tuple of parameter/attribute/return names for which type description
        matching is ignored. Ignored when `type_or_desc="description".
    """
    skipped = []
    for item_name, docstrings_grouped in items_docs.items():
        # If item not found in all objects, skip
        if sum([len(objs) for objs in docstrings_grouped.values()]) < n_objects:
            skipped.append(item_name)
        # If regex provided, match to all descriptions
        elif type_or_desc == "description" and descr_regex_pattern:
            not_matched = []
            for docstring, group in docstrings_grouped.items():
                if not re.search(descr_regex_pattern, docstring):
                    not_matched.extend(group)
            if not_matched:
                msg = textwrap.fill(
                    f"The description of {section[:-1]} '{item_name}' in {not_matched}"
                    f" does not match 'descr_regex_pattern': {descr_regex_pattern} "
                )
                raise AssertionError(msg)
        # Skip type checking for items in `ignore_types`
        elif type_or_desc == "type specification" and item_name in ignore_types:
            continue
        # Otherwise, if more than one key, docstrings not consistent between objects
        elif len(docstrings_grouped.keys()) > 1:
            msg_diff = _get_diff_msg(docstrings_grouped)
            obj_groups = " and ".join(
                str(group) for group in docstrings_grouped.values()
            )
            msg = textwrap.fill(
                f"The {type_or_desc} of {section[:-1]} '{item_name}' is inconsistent "
                f"between {obj_groups}:"
            )
            msg += msg_diff
            raise AssertionError(msg)
    if skipped:
        warnings.warn(
            f"Checking was skipped for {section}: {skipped} as they were "
            "not found in all objects."
        )