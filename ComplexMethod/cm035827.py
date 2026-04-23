def _sanitize_spec(spec: dict) -> dict:
    """Sanitize descriptions and summaries to be public-API friendly."""
    path_summary_overrides = {
        '/api/options/models': 'List Supported Models',
        '/api/options/agents': 'List Agents',
        '/api/options/security-analyzers': 'List Security Analyzers',
        '/api/conversations/{conversation_id}/list-files': 'List Workspace Files',
        '/api/conversations/{conversation_id}/select-file': 'Get File Content',
        '/api/conversations/{conversation_id}/zip-directory': 'Download Workspace Archive',
    }
    path_description_overrides = {
        '/api/options/models': 'List model identifiers available on this server based on configured providers.',
        '/api/options/agents': 'List available agent types supported by this server.',
        '/api/options/security-analyzers': 'List supported security analyzers.',
        '/api/conversations/{conversation_id}/list-files': 'List workspace files visible to the conversation runtime. Applies .gitignore and internal ignore rules.',
        '/api/conversations/{conversation_id}/select-file': 'Return the content of the given file from the conversation workspace.',
        '/api/conversations/{conversation_id}/zip-directory': 'Return a ZIP archive of the current conversation workspace.',
    }

    for path, methods in list(spec.get('paths', {}).items()):
        for method, meta in list(methods.items()):
            if not isinstance(meta, dict):
                continue
            # Override overly specific summaries where helpful
            if path in path_summary_overrides:
                meta['summary'] = path_summary_overrides[path]
            # Override description if provided; otherwise sanitize
            if path in path_description_overrides:
                meta['description'] = path_description_overrides[path]
            elif 'description' in meta and isinstance(meta['description'], str):
                meta['description'] = _sanitize_description(meta['description'])

    return spec