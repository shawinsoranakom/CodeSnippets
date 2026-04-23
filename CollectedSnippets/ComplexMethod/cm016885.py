def execute(cls, image_target, image_ref, method, source_stats, strength=1.0) -> io.NodeOutput:
        stats_mode = source_stats["source_stats"]
        target_index = source_stats.get("target_index", 0)

        if strength == 0 or image_ref is None:
            return io.NodeOutput(image_target)

        device = comfy.model_management.get_torch_device()
        intermediate_device = comfy.model_management.intermediate_device()
        intermediate_dtype = comfy.model_management.intermediate_dtype()

        B, H, W, C = image_target.shape
        B_ref = image_ref.shape[0]
        pbar = comfy.utils.ProgressBar(B)
        out = torch.empty(B, H, W, C, device=intermediate_device, dtype=intermediate_dtype)

        if method == 'histogram':
            uniform_lut = cls._build_histogram_transform(
                image_target, image_ref, device, stats_mode, target_index, B)

            for i in range(B):
                src = image_target[i].to(device, dtype=torch.float32).permute(2, 0, 1)
                src_flat = src.reshape(C, -1)
                if uniform_lut is not None:
                    lut = uniform_lut
                else:
                    ri = min(i, B_ref - 1)
                    ref = image_ref[ri].to(device, dtype=torch.float32).permute(2, 0, 1).reshape(C, -1)
                    lut = cls._histogram_lut(src_flat, ref)
                bin_idx = (src_flat * 255).long().clamp(0, 255)
                matched = lut.gather(1, bin_idx).view(C, H, W)
                result = matched if strength == 1.0 else torch.lerp(src, matched, strength)
                out[i] = result.permute(1, 2, 0).clamp_(0, 1).to(device=intermediate_device, dtype=intermediate_dtype)
                pbar.update(1)
        else:
            transform = cls._build_lab_transform(image_target, image_ref, device, stats_mode, target_index, is_reinhard=method == "reinhard_lab")

            for i in range(B):
                src_frame = cls._to_lab(image_target, i, device)
                corrected = transform(src_frame.view(C, -1), frame_idx=i)
                if strength == 1.0:
                    result = kornia.color.lab_to_rgb(corrected.view(1, C, H, W))
                else:
                    result = kornia.color.lab_to_rgb(torch.lerp(src_frame, corrected.view(1, C, H, W), strength))
                out[i] = result.squeeze(0).permute(1, 2, 0).clamp_(0, 1).to(device=intermediate_device, dtype=intermediate_dtype)
                pbar.update(1)

        return io.NodeOutput(out)