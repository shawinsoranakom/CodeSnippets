def get_mrope_input_positions(
        self,
        input_tokens: list[int],
        mm_features: list[MultiModalFeatureSpec],
    ) -> tuple[torch.Tensor, int]:
        """
        Compute M-RoPE input positions using mm_features directly.

        Example for use_audio_in_video case:
            (V_i are vision position ids, A_i are audio position ids)

            |V_1 ...    V_n|A_1 ...   A_n|V_n+1 ... V_2n|A_n+1 ... A_2n|...
            |vision chunk 1|audio chunk 1|vision chunk 2|audio chunk 2 |...
        """
        llm_pos_ids_list: list[np.ndarray] = []
        st = 0

        for offset, modality, data in self.iter_mm_features(mm_features):
            # Add text segment before this feature
            text_len = offset - st
            st_idx = int(llm_pos_ids_list[-1].max()) + 1 if llm_pos_ids_list else 0
            if text_len > 0:
                llm_pos_ids_list.append(
                    np.broadcast_to(np.arange(text_len), (3, text_len)) + st_idx
                )
                st_idx += text_len

            if modality == "audio":
                # Standalone audio positions
                audio_tokens = self._compute_audio_token_count(
                    data["audio_feature_length"]
                )
                llm_pos_ids_list.append(
                    np.broadcast_to(np.arange(audio_tokens), (3, audio_tokens)) + st_idx
                )
                st = offset + audio_tokens

            elif modality == "image":
                # Image uses np.indices like Qwen2-VL
                grid_t = data["grid_t"]
                grid_h = data["grid_h"]
                grid_w = data["grid_w"]
                t_factor = data["t_factor"]

                grid_indices = np.indices((grid_t, grid_h, grid_w))
                if t_factor != 1.0:
                    grid_indices[0] = (grid_indices[0] * t_factor).astype(np.int64)
                llm_pos_ids_list.append(grid_indices.reshape(3, -1) + st_idx)
                st = offset + grid_t * grid_h * grid_w

            elif modality == "video":
                grid_t = data["grid_t"]
                grid_h = data["grid_h"]
                grid_w = data["grid_w"]
                t_factor = data["t_factor"]

                if not data["use_audio_in_video"]:
                    # Simple video (same as Qwen2-VL)
                    grid_indices = np.indices((grid_t, grid_h, grid_w))
                    if t_factor != 1.0:
                        grid_indices[0] = (grid_indices[0] * t_factor).astype(np.int64)
                    llm_pos_ids_list.append(grid_indices.reshape(3, -1) + st_idx)
                    st = offset + grid_t * grid_h * grid_w
                else:
                    # Interleaved video+audio
                    pos_ids, token_count = self._compute_interleaved_positions(
                        st_idx, data
                    )
                    llm_pos_ids_list.append(pos_ids)
                    st = offset + token_count

        # Add trailing text
        if st < len(input_tokens):
            st_idx = int(llm_pos_ids_list[-1].max()) + 1 if llm_pos_ids_list else 0
            text_len = len(input_tokens) - st
            llm_pos_ids_list.append(
                np.broadcast_to(np.arange(text_len), (3, text_len)) + st_idx
            )

        llm_positions = np.concatenate(llm_pos_ids_list, axis=1).reshape(3, -1)
        mrope_position_delta = int(llm_positions.max()) + 1 - len(input_tokens)

        return torch.from_numpy(llm_positions), mrope_position_delta