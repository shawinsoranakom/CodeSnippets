def patch_shaders():
    """Patch shaders from this folder back into blueprint JSONs."""
    # Build lookup: blueprint_name -> [(node_id, shader_code), ...]
    shader_updates = {}

    for frag_path in sorted(GLSL_DIR.glob("*.frag")):
        # Parse filename: {blueprint_name}_{node_id}.frag
        parts = frag_path.stem.rsplit('_', 1)
        if len(parts) != 2:
            logger.warning("Skipping %s: invalid filename format", frag_path.name)
            continue

        blueprint_name, node_id_str = parts

        try:
            node_id = int(node_id_str)
        except ValueError:
            logger.warning("Skipping %s: invalid node_id", frag_path.name)
            continue

        with open(frag_path, 'r') as f:
            shader_code = f.read()

        if blueprint_name not in shader_updates:
            shader_updates[blueprint_name] = []
        shader_updates[blueprint_name].append((node_id, shader_code))

    # Apply updates to JSON files
    patched = 0
    for json_path in get_blueprint_files():
        blueprint_name = sanitize_filename(json_path.stem)

        if blueprint_name not in shader_updates:
            continue

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error reading %s: %s", json_path.name, e)
            continue

        modified = False
        for node_id, shader_code in shader_updates[blueprint_name]:
            # Find the node and update
            for subgraph in data.get('definitions', {}).get('subgraphs', []):
                for node in subgraph.get('nodes', []):
                    if node.get('id') == node_id and node.get('type') == 'GLSLShader':
                        widgets = node.get('widgets_values', [])
                        if len(widgets) > 0 and widgets[0] != shader_code:
                            widgets[0] = shader_code
                            modified = True
                            logger.info("  Patched: %s (node %d)", json_path.name, node_id)
                            patched += 1

        if modified:
            with open(json_path, 'w') as f:
                json.dump(data, f)

    if patched == 0:
        logger.info("No changes to apply.")
    else:
        logger.info("\nPatched %d shader(s)", patched)