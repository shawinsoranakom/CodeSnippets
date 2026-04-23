def check_all_objects_are_documented():
    """Check all models are properly documented."""
    documented_objs, documented_methods_map = find_all_documented_objects()
    modules = transformers._modules
    # the objects with the following prefixes are not required to be in the docs
    ignore_prefixes = [
        "_",  # internal objects
    ]
    objects = [c for c in dir(transformers) if c not in modules and not any(c.startswith(p) for p in ignore_prefixes)]
    undocumented_objs = [c for c in objects if c not in documented_objs and not ignore_undocumented(c)]
    if len(undocumented_objs) > 0:
        raise Exception(
            "The following objects are in the public init, but not in the docs:\n - " + "\n - ".join(undocumented_objs)
        )
    check_model_type_doc_match()
    check_public_method_exists(documented_methods_map)