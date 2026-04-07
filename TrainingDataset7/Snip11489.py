def _traverse_ancestors(model, starting_instance):
    current_instance = starting_instance
    while current_instance is not None:
        ancestor_link = current_instance._meta.get_ancestor_link(model)
        if not ancestor_link:
            yield current_instance, None
            break
        ancestor = ancestor_link.get_cached_value(current_instance, None)
        yield current_instance, ancestor
        current_instance = ancestor