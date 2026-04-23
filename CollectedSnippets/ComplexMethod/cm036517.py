def processor(*args, text="", images=None, videos=None, **kwargs):
        if images is None:
            images = []
        else:
            images = [images] if isinstance(images, Image) else images
        if videos is None:
            videos = []
        else:
            videos = [videos] if isinstance(videos, np.ndarray) else videos
            videos = [[PIL.Image.fromarray(frame) for frame in vid] for vid in videos]

        prompt_start_and_end = {
            "qwen2": ("<|im_start|>user\n", "<|im_end|>\n"),
            "llama": ("<|start_header_id|>user<|end_header_id|>\n\n", "<|eot_id|>"),
            "gemma2": ("<start_of_turn>user\n", "<end_of_turn>\n"),
        }
        for start, end in prompt_start_and_end.values():
            if start in text and end in text:
                text = text.split(start)[1].split(end)[0]
                break

        images_message = [{"type": "image", "image": img} for img in images]
        videos_message = [{"type": "video", "video": vid} for vid in videos]

        messages = [
            {
                "role": "user",
                "content": [
                    *images_message,
                    *videos_message,
                    {"type": "text", "text": text},
                ],
            }
        ]

        input_ids, pixel_values, grid_thws = hf_model.model.preprocess_inputs(
            messages=messages, enable_thinking=True
        )
        inputs = {
            "inputs": input_ids,
            "pixel_values": pixel_values,
            "grid_thws": grid_thws,
        }
        return BatchFeature(data=inputs, tensor_type="pt")