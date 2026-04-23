def execute(cls, mode: DCValues, model, model_patch, positive, negative, vae, width, height, length, audio_encoder_output_1, motion_frame_count,
                start_image=None, previous_frames=None, audio_scale=None, clip_vision_output=None, audio_encoder_output_2=None, mask_1=None, mask_2=None) -> io.NodeOutput:

        if previous_frames is not None and previous_frames.shape[0] < motion_frame_count:
            raise ValueError("Not enough previous frames provided.")

        if mode["mode"] == "two_speakers":
            audio_encoder_output_2 = mode["audio_encoder_output_2"]
            mask_1 = mode["mask_1"]
            mask_2 = mode["mask_2"]

        if audio_encoder_output_2 is not None:
            if mask_1 is None or mask_2 is None:
                raise ValueError("Masks must be provided if two audio encoder outputs are used.")

        ref_masks = None
        if mask_1 is not None and mask_2 is not None:
            if audio_encoder_output_2 is None:
                raise ValueError("Second audio encoder output must be provided if two masks are used.")
            ref_masks = torch.cat([mask_1, mask_2])

        latent = torch.zeros([1, 16, ((length - 1) // 4) + 1, height // 8, width // 8], device=comfy.model_management.intermediate_device())
        if start_image is not None:
            start_image = comfy.utils.common_upscale(start_image[:length].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
            image = torch.ones((length, height, width, start_image.shape[-1]), device=start_image.device, dtype=start_image.dtype) * 0.5
            image[:start_image.shape[0]] = start_image

            concat_latent_image = vae.encode(image[:, :, :, :3])
            concat_mask = torch.ones((1, 1, latent.shape[2], concat_latent_image.shape[-2], concat_latent_image.shape[-1]), device=start_image.device, dtype=start_image.dtype)
            concat_mask[:, :, :((start_image.shape[0] - 1) // 4) + 1] = 0.0

            positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": concat_latent_image, "concat_mask": concat_mask})
            negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": concat_latent_image, "concat_mask": concat_mask})

        if clip_vision_output is not None:
            positive = node_helpers.conditioning_set_values(positive, {"clip_vision_output": clip_vision_output})
            negative = node_helpers.conditioning_set_values(negative, {"clip_vision_output": clip_vision_output})

        model_patched = model.clone()

        encoded_audio_list = []
        seq_lengths = []

        for audio_encoder_output in [audio_encoder_output_1, audio_encoder_output_2]:
            if audio_encoder_output is None:
                continue
            all_layers = audio_encoder_output["encoded_audio_all_layers"]
            encoded_audio = torch.stack(all_layers, dim=0).squeeze(1)[1:]  # shape: [num_layers, T, 512]
            encoded_audio = linear_interpolation(encoded_audio, input_fps=50, output_fps=25).movedim(0, 1) # shape: [T, num_layers, 512]
            encoded_audio_list.append(encoded_audio)
            seq_lengths.append(encoded_audio.shape[0])

        # Pad / combine depending on multi_audio_type
        multi_audio_type = "add"
        if len(encoded_audio_list) > 1:
            if multi_audio_type == "para":
                max_len = max(seq_lengths)
                padded = []
                for emb in encoded_audio_list:
                    if emb.shape[0] < max_len:
                        pad = torch.zeros(max_len - emb.shape[0], *emb.shape[1:], dtype=emb.dtype)
                        emb = torch.cat([emb, pad], dim=0)
                    padded.append(emb)
                encoded_audio_list = padded
            elif multi_audio_type == "add":
                total_len = sum(seq_lengths)
                full_list = []
                offset = 0
                for emb, seq_len in zip(encoded_audio_list, seq_lengths):
                    full = torch.zeros(total_len, *emb.shape[1:], dtype=emb.dtype)
                    full[offset:offset+seq_len] = emb
                    full_list.append(full)
                    offset += seq_len
                encoded_audio_list = full_list

        token_ref_target_masks = None
        if ref_masks is not None:
            token_ref_target_masks = torch.nn.functional.interpolate(
                ref_masks.unsqueeze(0), size=(latent.shape[-2] // 2, latent.shape[-1] // 2), mode='nearest')[0]
            token_ref_target_masks = (token_ref_target_masks > 0).view(token_ref_target_masks.shape[0], -1)

        # when extending from previous frames
        if previous_frames is not None:
            motion_frames = comfy.utils.common_upscale(previous_frames[-motion_frame_count:].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
            frame_offset = previous_frames.shape[0] - motion_frame_count

            audio_start = frame_offset
            audio_end = audio_start + length
            logging.info(f"InfiniteTalk: Processing audio frames {audio_start} - {audio_end}")

            motion_frames_latent = vae.encode(motion_frames[:, :, :, :3])
            trim_image = motion_frame_count
        else:
            audio_start = trim_image = 0
            audio_end = length
            motion_frames_latent = concat_latent_image[:, :, :1]

        audio_embed = project_audio_features(model_patch.model.audio_proj, encoded_audio_list, audio_start, audio_end).to(model_patched.model_dtype())
        model_patched.model_options["transformer_options"]["audio_embeds"] = audio_embed

        # add outer sample wrapper
        model_patched.add_wrapper_with_key(
            comfy.patcher_extension.WrappersMP.OUTER_SAMPLE,
            "infinite_talk_outer_sample",
            InfiniteTalkOuterSampleWrapper(
                motion_frames_latent,
                model_patch,
                is_extend=previous_frames is not None,
            ))
        # add cross-attention patch
        model_patched.set_model_patch(MultiTalkCrossAttnPatch(model_patch, audio_scale), "attn2_patch")
        if token_ref_target_masks is not None:
            model_patched.set_model_patch(MultiTalkGetAttnMapPatch(token_ref_target_masks), "attn1_patch")

        out_latent = {}
        out_latent["samples"] = latent
        return io.NodeOutput(model_patched, positive, negative, out_latent, trim_image)