def add_annotations(app: Sphinx, doctree: nodes.document) -> None:
    state = app.env.domaindata["c_annotations"]
    refcount_data = state["refcount_data"]
    stable_abi_data = state["stable_abi_data"]
    threadsafety_data = state["threadsafety_data"]
    for node in doctree.findall(addnodes.desc_content):
        par = node.parent
        if par["domain"] != "c":
            continue
        if not par[0].get("ids", None):
            continue
        name = par[0]["ids"][0].removeprefix("c.")
        objtype = par["objtype"]

        # Thread safety annotation — inserted first so it appears last (bottom-most)
        # among all annotations.
        if entry := threadsafety_data.get(name):
            annotation = _threadsafety_annotation(entry.level)
            node.insert(0, annotation)

        # Stable ABI annotation.
        if record := stable_abi_data.get(name):
            if ROLE_TO_OBJECT_TYPE[record.role] != objtype:
                msg = (
                    f"Object type mismatch in limited API annotation for {name}: "
                    f"{ROLE_TO_OBJECT_TYPE[record.role]!r} != {objtype!r}"
                )
                raise ValueError(msg)
            annotation = _stable_abi_annotation(record)
            node.insert(0, annotation)

        # Unstable API annotation.
        if name.startswith("PyUnstable"):
            annotation = _unstable_api_annotation()
            node.insert(0, annotation)

        # Return value annotation
        if objtype != "function":
            continue
        if name not in refcount_data:
            continue
        entry = refcount_data[name]
        if not entry.result_type.endswith("Object*"):
            continue
        annotation = _return_value_annotation(entry.result_refs)
        node.insert(0, annotation)