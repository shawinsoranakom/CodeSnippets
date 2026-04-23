def hook(value, total, preview_image, prompt_id=None, node_id=None):
        executing_context = get_executing_context()
        if prompt_id is None and executing_context is not None:
            prompt_id = executing_context.prompt_id
        if node_id is None and executing_context is not None:
            node_id = executing_context.node_id
        comfy.model_management.throw_exception_if_processing_interrupted()
        if prompt_id is None:
            prompt_id = server_instance.last_prompt_id
        if node_id is None:
            node_id = server_instance.last_node_id
        progress = {"value": value, "max": total, "prompt_id": prompt_id, "node": node_id}
        get_progress_state().update_progress(node_id, value, total, preview_image)

        server_instance.send_sync("progress", progress, server_instance.client_id)
        if preview_image is not None:
            # Only send old method if client doesn't support preview metadata
            if not feature_flags.supports_feature(
                server_instance.sockets_metadata,
                server_instance.client_id,
                "supports_preview_metadata",
            ):
                server_instance.send_sync(
                    BinaryEventTypes.UNENCODED_PREVIEW_IMAGE,
                    preview_image,
                    server_instance.client_id,
                )