def get_or_create_path(abs_path: str, base_path: str):
        parts = abs_path.rstrip("/").replace("//", "/").split("/")
        parent_id = ""
        if len(parts) > 1:
            parent_path = "/".join(parts[:-1])
            parent = get_or_create_path(parent_path, base_path=base_path)
            parent_id = parent.id
        if existing := [
            r
            for r in rest_api.resources.values()
            if r.path_part == (parts[-1] or "/") and (r.parent_id or "") == (parent_id or "")
        ]:
            return existing[0]

        # construct relative path (without base path), then add field resources for this path
        rel_path = abs_path.removeprefix(base_path)
        return add_path_methods(rel_path, parts, parent_id=parent_id)