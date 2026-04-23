def get_needed_imports(body: dict[str, dict], all_imports: list[cst.CSTNode]) -> list[cst.CSTNode]:
    """Get all the imports needed in the `body`, from the list of `all_imports`.
    `body` is a dict with the following structure `{str: {"insert_idx": int, "node": cst.CSTNode}}`.
    Note: we need to use `isinstance` on scope assignments, m.matches apparently does not work here yet!
    """
    new_body = [k[1]["node"] for k in sorted(body.items(), key=lambda x: x[1]["insert_idx"])]
    wrapper = MetadataWrapper(cst.Module(body=all_imports + new_body))
    scopes = set(wrapper.resolve(ScopeProvider).values())
    unused_imports = set()
    import_ref_count = defaultdict(lambda: 0)
    for scope in scopes:
        for assignment in scope.assignments:
            node = assignment.node
            if isinstance(assignment, cst.metadata.Assignment) and isinstance(node, (cst.Import, cst.ImportFrom)):
                ref_count = len(assignment.references)
                name = assignment.name
                import_ref_count[name] = max(ref_count, import_ref_count[name])
    # Similar imports may be redefined, and only used between their 1st and 2nd definition so if we already have
    # a ref count > 0 at any point, the imports is actually used
    unused_imports = {name for name, count in import_ref_count.items() if count <= 0 or name in body}

    imports_to_keep = []
    # We need to keep track of which names were already imported, because some import may be duplicated from multiple sources
    # or be both protected and unprotected due to inconsistency between models
    added_names = set()
    existing_protected_statements = set()  # str repr of the import nodes - does not work with the nodes directly
    for node in all_imports:
        if m.matches(node, m.If()):  # handle safe imports
            new_statements = []
            for stmt_node in node.body.body:
                append_new_import_node(stmt_node, unused_imports, added_names, new_statements)
            new_statements = [stmt for stmt in new_statements if str(stmt) not in existing_protected_statements]
            if len(new_statements) > 0:
                new_node = node.with_changes(body=node.body.with_changes(body=new_statements))
                imports_to_keep.append(new_node)
                existing_protected_statements.update({str(stmt) for stmt in new_statements})
        else:
            append_new_import_node(node, unused_imports, added_names, imports_to_keep)

    protected_import_nodes = [node for node in imports_to_keep if m.matches(node, m.If())]
    usual_import_nodes = [node for node in imports_to_keep if not m.matches(node, m.If())]

    # Protected imports always appear at the end of all imports
    return usual_import_nodes + protected_import_nodes