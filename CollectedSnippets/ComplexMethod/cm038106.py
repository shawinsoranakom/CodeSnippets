def get_mrope_input_positions(
        self,
        input_tokens: list[int],
        mm_features: list[MultiModalFeatureSpec],
    ) -> tuple[torch.Tensor, int]:
        """Compute M-RoPE input positions using mm_features directly."""
        seq_len = len(input_tokens)

        llm_pos_ids_list: list[np.ndarray] = []
        st = 0

        for offset, modality, data in self.iter_mm_features(mm_features):
            text_len = offset - st
            st_idx = int(llm_pos_ids_list[-1].max()) + 1 if llm_pos_ids_list else 0

            if text_len > 0:
                llm_pos_ids_list.append(
                    np.broadcast_to(np.arange(text_len), (3, text_len)) + st_idx
                )
                st_idx += text_len

            bos_pos = np.broadcast_to(np.array([st_idx]), (3, 1))
            llm_pos_ids_list.append(bos_pos)
            st_idx += 1

            if modality == "audio":
                audio_tokens = self._compute_audio_token_count(
                    data["audio_feature_length"]
                )
                audio_pos = (
                    np.broadcast_to(np.arange(audio_tokens), (3, audio_tokens)) + st_idx
                )
                llm_pos_ids_list.append(audio_pos)
                st_idx = int(audio_pos.max()) + 1

                eos_pos = np.broadcast_to(np.array([st_idx]), (3, 1))
                llm_pos_ids_list.append(eos_pos)
                st = offset + 1 + audio_tokens + 1

            elif modality == "image":
                grid_t = data["grid_t"]
                grid_h = data["grid_h"]
                grid_w = data["grid_w"]
                t_factor = data["t_factor"]

                grid_indices = np.indices((grid_t, grid_h, grid_w))
                if t_factor != 1.0:
                    grid_indices[0] = (grid_indices[0] * t_factor).astype(np.int64)
                llm_pos_ids_list.append(grid_indices.reshape(3, -1) + st_idx)

                image_len = grid_t * grid_h * grid_w
                st_idx = int(llm_pos_ids_list[-1].max()) + 1

                eos_pos = np.broadcast_to(np.array([st_idx]), (3, 1))
                llm_pos_ids_list.append(eos_pos)
                st = offset + 1 + image_len + 1

            elif modality == "video":
                grid_t = data["grid_t"]
                grid_h = data["grid_h"]
                grid_w = data["grid_w"]
                t_factor = data["t_factor"]

                if not data["use_audio_in_video"]:
                    grid_indices = np.indices((grid_t, grid_h, grid_w))
                    if t_factor != 1.0:
                        grid_indices[0] = (grid_indices[0] * t_factor).astype(np.int64)
                    llm_pos_ids_list.append(grid_indices.reshape(3, -1) + st_idx)

                    video_len = grid_t * grid_h * grid_w
                    st_idx = int(llm_pos_ids_list[-1].max()) + 1

                    eos_pos = np.broadcast_to(np.array([st_idx]), (3, 1))
                    llm_pos_ids_list.append(eos_pos)
                    st = offset + 1 + video_len + 1
                else:
                    audio_bos_pos = np.broadcast_to(np.array([st_idx - 1]), (3, 1))
                    llm_pos_ids_list.append(audio_bos_pos)

                    pos_ids, _ = self._compute_interleaved_positions(st_idx, data)
                    llm_pos_ids_list.append(pos_ids)
                    st_idx = int(pos_ids.max()) + 1

                    eos_pos = np.broadcast_to(np.array([st_idx]), (3, 1))
                    llm_pos_ids_list.append(eos_pos)
                    llm_pos_ids_list.append(eos_pos)

                    video_len = grid_t * grid_h * grid_w
                    audio_len = self._compute_audio_token_count(
                        data["audio_feature_length"]
                    )
                    st = offset + 2 + video_len + audio_len + 2

        if st < seq_len:
            st_idx = int(llm_pos_ids_list[-1].max()) + 1 if llm_pos_ids_list else 0
            text_len = seq_len - st
            llm_pos_ids_list.append(
                np.broadcast_to(np.arange(text_len), (3, text_len)) + st_idx
            )

        llm_positions = np.concatenate(llm_pos_ids_list, axis=1).reshape(3, -1)
        if llm_positions.shape[1] != seq_len:
            raise RuntimeError("Position ids length mismatch with input ids length")

        mrope_position_delta = int(llm_positions.max()) + 1 - seq_len
        return torch.from_numpy(llm_positions), mrope_position_delta