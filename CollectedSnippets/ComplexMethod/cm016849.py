def execute(cls, interp_model, images, multiplier) -> io.NodeOutput:
        offload_device = model_management.intermediate_device()

        num_frames = images.shape[0]
        if num_frames < 2 or multiplier < 2:
            return io.NodeOutput(images)

        model_management.load_model_gpu(interp_model)
        device = interp_model.load_device
        dtype = interp_model.model_dtype()
        inference_model = interp_model.model

        # Free VRAM for inference activations (model weights + ~20x a single frame's worth)
        H, W = images.shape[1], images.shape[2]
        activation_mem = H * W * 3 * images.element_size() * 20
        model_management.free_memory(activation_mem, device)
        align = getattr(inference_model, "pad_align", 1)

        # Prepare a single padded frame on device for determining output dimensions
        def prepare_frame(idx):
            frame = images[idx:idx + 1].movedim(-1, 1).to(dtype=dtype, device=device)
            if align > 1:
                from comfy.ldm.common_dit import pad_to_patch_size
                frame = pad_to_patch_size(frame, (align, align), padding_mode="reflect")
            return frame

        # Count total interpolation passes for progress bar
        total_pairs = num_frames - 1
        num_interp = multiplier - 1
        total_steps = total_pairs * num_interp
        pbar = comfy.utils.ProgressBar(total_steps)
        tqdm_bar = tqdm(total=total_steps, desc="Frame interpolation")

        batch = num_interp  # reduced on OOM and persists across pairs (same resolution = same limit)
        t_values = [t / multiplier for t in range(1, multiplier)]

        out_dtype = model_management.intermediate_dtype()
        total_out_frames = total_pairs * multiplier + 1
        result = torch.empty((total_out_frames, 3, H, W), dtype=out_dtype, device=offload_device)
        result[0] = images[0].movedim(-1, 0).to(out_dtype)
        out_idx = 1

        # Pre-compute timestep tensor on device (padded dimensions needed)
        sample = prepare_frame(0)
        pH, pW = sample.shape[2], sample.shape[3]
        ts_full = torch.tensor(t_values, device=device, dtype=dtype).reshape(num_interp, 1, 1, 1)
        ts_full = ts_full.expand(-1, 1, pH, pW)
        del sample

        multi_fn = getattr(inference_model, "forward_multi_timestep", None)
        feat_cache = {}
        prev_frame = None

        try:
            for i in range(total_pairs):
                img0_single = prev_frame if prev_frame is not None else prepare_frame(i)
                img1_single = prepare_frame(i + 1)
                prev_frame = img1_single

                # Cache features: img1 of pair N becomes img0 of pair N+1
                feat_cache["img0"] = feat_cache.pop("next") if "next" in feat_cache else inference_model.extract_features(img0_single)
                feat_cache["img1"] = inference_model.extract_features(img1_single)
                feat_cache["next"] = feat_cache["img1"]

                used_multi = False
                if multi_fn is not None:
                    # Models with timestep-independent flow can compute it once for all timesteps
                    try:
                        mids = multi_fn(img0_single, img1_single, t_values, cache=feat_cache)
                        result[out_idx:out_idx + num_interp] = mids[:, :, :H, :W].to(out_dtype)
                        out_idx += num_interp
                        pbar.update(num_interp)
                        tqdm_bar.update(num_interp)
                        used_multi = True
                    except model_management.OOM_EXCEPTION:
                        model_management.soft_empty_cache()
                        multi_fn = None  # fall through to single-timestep path

                if not used_multi:
                    j = 0
                    while j < num_interp:
                        b = min(batch, num_interp - j)
                        try:
                            img0 = img0_single.expand(b, -1, -1, -1)
                            img1 = img1_single.expand(b, -1, -1, -1)
                            mids = inference_model(img0, img1, timestep=ts_full[j:j + b], cache=feat_cache)
                            result[out_idx:out_idx + b] = mids[:, :, :H, :W].to(out_dtype)
                            out_idx += b
                            pbar.update(b)
                            tqdm_bar.update(b)
                            j += b
                        except model_management.OOM_EXCEPTION:
                            if batch <= 1:
                                raise
                            batch = max(1, batch // 2)
                            model_management.soft_empty_cache()

                result[out_idx] = images[i + 1].movedim(-1, 0).to(out_dtype)
                out_idx += 1
        finally:
            tqdm_bar.close()

        # BCHW -> BHWC
        result = result.movedim(1, -1).clamp_(0.0, 1.0)
        return io.NodeOutput(result)