def execute(cls, image, bboxes, output_width, output_height, padding, keep_aspect="stretch") -> io.NodeOutput:
        total_frames = image.shape[0]
        img_h = image.shape[1]
        img_w = image.shape[2]
        num_ch = image.shape[3]

        if not isinstance(bboxes, list):
            bboxes = [[bboxes]]
        elif len(bboxes) == 0:
            return io.NodeOutput(image)

        crops = []

        for frame_idx in range(total_frames):
            frame_bboxes = bboxes[min(frame_idx, len(bboxes) - 1)]
            if not frame_bboxes:
                continue

            frame_chw = image[frame_idx].permute(2, 0, 1).unsqueeze(0)  # BHWC → BCHW (1, C, H, W)

            # Union all bboxes for this frame into a single crop region
            x1 = min(int(b["x"]) for b in frame_bboxes)
            y1 = min(int(b["y"]) for b in frame_bboxes)
            x2 = max(int(b["x"] + b["width"])  for b in frame_bboxes)
            y2 = max(int(b["y"] + b["height"]) for b in frame_bboxes)

            if padding > 0:
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(img_w, x2 + padding)
                y2 = min(img_h, y2 + padding)

            x1, x2 = max(0, x1), min(img_w, x2)
            y1, y2 = max(0, y1), min(img_h, y2)

            # Fallback for empty/degenerate crops
            if x2 <= x1 or y2 <= y1:
                fallback_size = int(min(img_h, img_w) * 0.3)
                fb_x1 = max(0, (img_w - fallback_size) // 2)
                fb_y1 = max(0, int(img_h * 0.1))
                fb_x2 = min(img_w, fb_x1 + fallback_size)
                fb_y2 = min(img_h, fb_y1 + fallback_size)
                if fb_x2 <= fb_x1 or fb_y2 <= fb_y1:
                    crops.append(torch.zeros(1, num_ch, output_height, output_width, dtype=image.dtype, device=image.device))
                    continue
                x1, y1, x2, y2 = fb_x1, fb_y1, fb_x2, fb_y2

            crop_chw = frame_chw[:, :, y1:y2, x1:x2]  # (1, C, crop_h, crop_w)

            if keep_aspect == "pad":
                crop_h, crop_w = y2 - y1, x2 - x1
                scale = min(output_width / crop_w, output_height / crop_h)
                scaled_w = int(round(crop_w * scale))
                scaled_h = int(round(crop_h * scale))
                scaled = comfy.utils.common_upscale(crop_chw, scaled_w, scaled_h, upscale_method="bilinear", crop="disabled")
                pad_left = (output_width  - scaled_w) // 2
                pad_top  = (output_height - scaled_h) // 2
                resized = torch.zeros(1, num_ch, output_height, output_width, dtype=image.dtype, device=image.device)
                resized[:, :, pad_top:pad_top + scaled_h, pad_left:pad_left + scaled_w] = scaled
            else:  # "stretch"
                resized = comfy.utils.common_upscale(crop_chw, output_width, output_height, upscale_method="bilinear", crop="disabled")
            crops.append(resized)

        if not crops:
            return io.NodeOutput(image)

        out_images = torch.cat(crops, dim=0).permute(0, 2, 3, 1)  # (N, H, W, C)
        return io.NodeOutput(out_images)