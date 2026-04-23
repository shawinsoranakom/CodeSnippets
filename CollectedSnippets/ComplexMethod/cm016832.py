def execute(
        cls,
        fragment_shader: str,
        size_mode: SizeModeInput,
        images: io.Autogrow.Type,
        floats: io.Autogrow.Type = None,
        ints: io.Autogrow.Type = None,
        bools: io.Autogrow.Type = None,
        curves: io.Autogrow.Type = None,
        **kwargs,
    ) -> io.NodeOutput:

        image_list = [v for v in images.values() if v is not None]
        float_list = (
            [v if v is not None else 0.0 for v in floats.values()] if floats else []
        )
        int_list = [v if v is not None else 0 for v in ints.values()] if ints else []
        bool_list = [v if v is not None else False for v in bools.values()] if bools else []

        curve_luts = [v.to_lut().astype(np.float32) for v in curves.values() if v is not None] if curves else []

        if not image_list:
            raise ValueError("At least one input image is required")

        # Determine output dimensions
        if size_mode["size_mode"] == "custom":
            out_width = size_mode["width"]
            out_height = size_mode["height"]
        else:
            out_height, out_width = image_list[0].shape[1:3]

        batch_size = image_list[0].shape[0]

        # Prepare batches
        image_batches = []
        for batch_idx in range(batch_size):
            batch_images = [img_tensor[batch_idx].cpu().numpy().astype(np.float32) for img_tensor in image_list]
            image_batches.append(batch_images)

        all_batch_outputs = _render_shader_batch(
            fragment_shader,
            out_width,
            out_height,
            image_batches,
            float_list,
            int_list,
            bool_list,
            curve_luts,
        )

        # Collect outputs into tensors
        all_outputs = [[] for _ in range(MAX_OUTPUTS)]
        for batch_outputs in all_batch_outputs:
            for i, out_img in enumerate(batch_outputs):
                all_outputs[i].append(torch.from_numpy(out_img))

        output_tensors = [torch.stack(all_outputs[i], dim=0) for i in range(MAX_OUTPUTS)]
        return io.NodeOutput(
            *output_tensors,
            ui=cls._build_ui_output(image_list, output_tensors[0]),
        )