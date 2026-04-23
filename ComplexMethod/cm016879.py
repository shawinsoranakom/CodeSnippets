def execute(cls, model, vae, image, batch_size, bboxes=None) -> io.NodeOutput:

        height, width = image.shape[-3], image.shape[-2]
        context = LotusConditioning().execute().result[0]

        # Use output_block_patch to capture the last 640-channel feature
        def output_patch(h, hsp, transformer_options):
            nonlocal captured_feat
            if h.shape[1] == 640:  # Capture the features for wholebody
                captured_feat = h.clone()
            return h, hsp

        model_clone = model.clone()
        model_clone.model_options["transformer_options"] = {"patches": {"output_block_patch": [output_patch]}}

        if not hasattr(model.model.diffusion_model, 'heatmap_head'):
            raise ValueError("The provided model does not have a heatmap_head. Please use SDPose model from here https://huggingface.co/Comfy-Org/SDPose/tree/main/checkpoints.")

        head = model.model.diffusion_model.heatmap_head
        total_images = image.shape[0]
        captured_feat = None

        model_h = int(head.heatmap_size[0]) * 4   # e.g. 192 * 4 = 768
        model_w = int(head.heatmap_size[1]) * 4   # e.g. 256 * 4 = 1024

        def _resize_to_model(imgs):
            """Aspect-preserving resize + zero-pad BHWC images to (model_h, model_w). Returns (resized_bhwc, scale, pad_top, pad_left)."""
            h, w = imgs.shape[-3], imgs.shape[-2]
            scale = min(model_h / h, model_w / w)
            sh, sw = int(round(h * scale)), int(round(w * scale))
            pt, pl = (model_h - sh) // 2, (model_w - sw) // 2
            chw = imgs.permute(0, 3, 1, 2).float()
            scaled = comfy.utils.common_upscale(chw, sw, sh, upscale_method="bilinear", crop="disabled")
            padded = torch.zeros(scaled.shape[0], scaled.shape[1], model_h, model_w, dtype=scaled.dtype, device=scaled.device)
            padded[:, :, pt:pt + sh, pl:pl + sw] = scaled
            return padded.permute(0, 2, 3, 1), scale, pt, pl

        def _remap_keypoints(kp, scale, pad_top, pad_left, offset_x=0, offset_y=0):
            """Remap keypoints from model space back to original image space."""
            kp = kp.copy() if isinstance(kp, np.ndarray) else np.array(kp, dtype=np.float32)
            invalid = kp[..., 0] < 0
            kp[..., 0] = (kp[..., 0] - pad_left) / scale + offset_x
            kp[..., 1] = (kp[..., 1] - pad_top)  / scale + offset_y
            kp[invalid] = -1
            return kp

        def _run_on_latent(latent_batch):
            """Run one forward pass and return (keypoints_list, scores_list) for the batch."""
            nonlocal captured_feat
            captured_feat = None
            _ = comfy.sample.sample(
                model_clone,
                noise=torch.zeros_like(latent_batch),
                steps=1, cfg=1.0,
                sampler_name="euler", scheduler="simple",
                positive=context, negative=context,
                latent_image=latent_batch, disable_noise=True, disable_pbar=True,
            )
            return head(captured_feat)  # keypoints_batch, scores_batch

        # all_keypoints / all_scores are lists-of-lists:
        #   outer index = input image index
        #   inner index = detected person (one per bbox, or one for full-image)
        all_keypoints = []  # shape: [n_images][n_persons]
        all_scores = []     # shape: [n_images][n_persons]
        pbar = comfy.utils.ProgressBar(total_images)

        if bboxes is not None:
            if not isinstance(bboxes, list):
                bboxes = [[bboxes]]
            elif len(bboxes) == 0:
                bboxes = [None] * total_images
            # --- bbox-crop mode: one forward pass per crop -------------------------
            for img_idx in tqdm(range(total_images), desc="Extracting keypoints from crops"):
                img = image[img_idx:img_idx + 1]  # (1, H, W, C)
                # Broadcasting: if fewer bbox lists than images, repeat the last one.
                img_bboxes = bboxes[min(img_idx, len(bboxes) - 1)] if bboxes else None

                img_keypoints = []
                img_scores = []

                if img_bboxes:
                    for bbox in img_bboxes:
                        x1 = max(0, int(bbox["x"]))
                        y1 = max(0, int(bbox["y"]))
                        x2 = min(width,  int(bbox["x"] + bbox["width"]))
                        y2 = min(height, int(bbox["y"] + bbox["height"]))

                        if x2 <= x1 or y2 <= y1:
                            continue

                        crop = img[:, y1:y2, x1:x2, :]  # (1, crop_h, crop_w, C)
                        crop_resized, scale, pad_top, pad_left = _resize_to_model(crop)

                        latent_crop = vae.encode(crop_resized)
                        kp_batch, sc_batch = _run_on_latent(latent_crop)
                        kp = _remap_keypoints(kp_batch[0], scale, pad_top, pad_left, x1, y1)
                        img_keypoints.append(kp)
                        img_scores.append(sc_batch[0])
                else:
                    img_resized, scale, pad_top, pad_left = _resize_to_model(img)
                    latent_img = vae.encode(img_resized)
                    kp_batch, sc_batch = _run_on_latent(latent_img)
                    img_keypoints.append(_remap_keypoints(kp_batch[0], scale, pad_top, pad_left))
                    img_scores.append(sc_batch[0])

                all_keypoints.append(img_keypoints)
                all_scores.append(img_scores)
                pbar.update(1)

        else: # full-image mode, batched
            for batch_start in tqdm(range(0, total_images, batch_size), desc="Extracting keypoints"):
                batch_resized, scale, pad_top, pad_left = _resize_to_model(image[batch_start:batch_start + batch_size])
                latent_batch = vae.encode(batch_resized)
                kp_batch, sc_batch = _run_on_latent(latent_batch)

                for kp, sc in zip(kp_batch, sc_batch):
                    all_keypoints.append([_remap_keypoints(kp, scale, pad_top, pad_left)])
                    all_scores.append([sc])

                pbar.update(len(kp_batch))

        openpose_frames = _to_openpose_frames(all_keypoints, all_scores, height, width)
        return io.NodeOutput(openpose_frames)