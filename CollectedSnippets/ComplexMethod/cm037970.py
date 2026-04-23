def get_replacement_keye(item_idx: int, modality: str):
            """
            Args:
                item_idx(int): The item index of modality to replace
                modality(str): The modality
            """
            if modality == "image":
                out_item = out_mm_kwargs[modality][item_idx]
                grid_thw = out_item[f"{modality}_grid_thw"].data
                assert isinstance(grid_thw, torch.Tensor)

                num_tokens = int(grid_thw.prod()) // merge_length
                return [image_token_id] * num_tokens
            elif modality == "video":
                placeholders = []
                video_timestamps = timestamps[item_idx]
                video_frame_types = frame_types[item_idx]
                grid_thw = video_grid_hws[
                    cu_seqlens[item_idx] : cu_seqlens[item_idx + 1]
                ]

                nframes = grid_thw.shape[0]

                if video_timestamps is None:
                    video_timestamps = [""] * nframes
                else:
                    video_timestamps = [format(ts, ".1f") for ts in video_timestamps]

                if video_frame_types is None:
                    video_frame_types = [0] * nframes
                for i, sub_thw in enumerate(grid_thw):
                    s = f"{hf_processor.frame_token}{video_timestamps[i]}"
                    if video_frame_types[i] == 1:
                        s += hf_processor.fast_start
                    placeholders.extend(tokenizer.encode(s))
                    num_frame_tokens = int(sub_thw.prod()) // merge_length
                    placeholders.extend([video_token_id] * num_frame_tokens)
                    if video_frame_types[i] == 1:
                        placeholders.append(vocab[hf_processor.fast_end])

                return PromptUpdateDetails.select_token_id(
                    placeholders, embed_token_id=video_token_id
                )
            else:
                raise ValueError(f"Unsupported modality {modality}")