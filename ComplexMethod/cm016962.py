async def execute(
        cls,
        original_model_task_id,
        format: str,
        quad: bool,
        force_symmetry: bool,
        face_limit: int,
        flatten_bottom: bool,
        flatten_bottom_threshold: float,
        texture_size: int,
        texture_format: str,
        pivot_to_center_bottom: bool,
        scale_factor: float,
        with_animation: bool,
        pack_uv: bool,
        bake: bool,
        part_names: str,
        fbx_preset: str,
        export_vertex_colors: bool,
        export_orientation: str,
        animate_in_place: bool,
    ) -> IO.NodeOutput:
        if not original_model_task_id:
            raise RuntimeError("original_model_task_id is required")

        # Parse part_names from comma-separated string to list
        part_names_list = None
        if part_names and part_names.strip():
            part_names_list = [name.strip() for name in part_names.split(',') if name.strip()]

        response = await sync_op(
            cls,
            endpoint=ApiEndpoint(path="/proxy/tripo/v2/openapi/task", method="POST"),
            response_model=TripoTaskResponse,
            data=TripoConvertModelRequest(
                original_model_task_id=original_model_task_id,
                format=format,
                quad=quad if quad else None,
                force_symmetry=force_symmetry if force_symmetry else None,
                face_limit=face_limit if face_limit != -1 else None,
                flatten_bottom=flatten_bottom if flatten_bottom else None,
                flatten_bottom_threshold=flatten_bottom_threshold if flatten_bottom_threshold != 0.0 else None,
                texture_size=texture_size if texture_size != 4096 else None,
                texture_format=texture_format if texture_format != "JPEG" else None,
                pivot_to_center_bottom=pivot_to_center_bottom if pivot_to_center_bottom else None,
                scale_factor=scale_factor if scale_factor != 1.0 else None,
                with_animation=with_animation if with_animation else None,
                pack_uv=pack_uv if pack_uv else None,
                bake=bake if bake else None,
                part_names=part_names_list,
                fbx_preset=fbx_preset if fbx_preset != "blender" else None,
                export_vertex_colors=export_vertex_colors if export_vertex_colors else None,
                export_orientation=export_orientation if export_orientation != "default" else None,
                animate_in_place=animate_in_place if animate_in_place else None,
            ),
        )
        return await poll_until_finished(cls, response, average_duration=30)