def apply_tweaks_on_vertex(vertex: Vertex, node_tweaks: dict[str, Any]) -> None:
    for tweak_name, tweak_value in node_tweaks.items():
        if tweak_name and tweak_value and tweak_name in vertex.params:
            vertex.params[tweak_name] = tweak_value

            # Determine if we should load from DB
            tweak_load_from_db = False
            if isinstance(tweak_value, dict):
                tweak_load_from_db = tweak_value.get("load_from_db", False)

            if tweak_load_from_db:
                if tweak_name not in vertex.load_from_db_fields:
                    vertex.load_from_db_fields.append(tweak_name)
            elif tweak_name in vertex.load_from_db_fields:
                vertex.load_from_db_fields.remove(tweak_name)