def extract_shaders():
    """Extract all shaders from blueprint JSONs to this folder."""
    extracted = 0
    for json_path in get_blueprint_files():
        blueprint_name = json_path.stem

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Skipping %s: %s", json_path.name, e)
            continue

        # Find GLSLShader nodes in subgraphs
        for subgraph in data.get('definitions', {}).get('subgraphs', []):
            for node in subgraph.get('nodes', []):
                if node.get('type') == 'GLSLShader':
                    node_id = node.get('id')
                    widgets = node.get('widgets_values', [])

                    # Find shader code (first string that looks like GLSL)
                    for widget in widgets:
                        if isinstance(widget, str) and widget.startswith('#version'):
                            safe_name = sanitize_filename(blueprint_name)
                            frag_name = f"{safe_name}_{node_id}.frag"
                            frag_path = GLSL_DIR / frag_name

                            with open(frag_path, 'w') as f:
                                f.write(widget)

                            logger.info("  Extracted: %s", frag_name)
                            extracted += 1
                            break

    logger.info("\nExtracted %d shader(s)", extracted)