def replace_multimodal_special_tokens(
        self,
        text,
        audio_lengths,
        image_grid_thw,
        video_grid_thw,
        video_second_per_grid,
        use_audio_in_video,
        position_id_per_seconds,
        seconds_per_chunk,
    ):
        # Extend mm token length
        merge_length_image = self.image_processor.merge_size**2
        merge_length_video = self.video_processor.merge_size**2

        processed_text = []
        for sample in text:
            positions = []
            special_tokens = [re.escape(tok) for tok in [self.audio_token, self.image_token, self.video_token]]
            pattern = "|".join(special_tokens)
            positions = sorted([(match.start(), match.group()) for match in re.finditer(pattern, sample)])
            positions.sort(key=lambda x: x[0])

            for _, special_token in positions:
                if special_token == self.audio_token:
                    sample = sample.replace(self.audio_token, "<|audio_placeholder|>" * next(audio_lengths), 1)
                elif special_token == self.image_token:
                    image_seq_length = next(image_grid_thw).prod() // merge_length_image
                    sample = sample.replace(self.image_token, "<|image_placeholder|>" * image_seq_length, 1)
                elif special_token == self.video_token:
                    if not use_audio_in_video:
                        video_seq_length = next(video_grid_thw).prod() // merge_length_video
                        sample = sample.replace(self.video_token, "<|video_placeholder|>" * video_seq_length, 1)
                    else:
                        audio_token_indices = np.arange(next(audio_lengths))
                        curr_video_grid_thw = next(video_grid_thw)
                        height = curr_video_grid_thw[1] // self.video_processor.merge_size
                        width = curr_video_grid_thw[2] // self.video_processor.merge_size
                        video_token_indices = np.arange(curr_video_grid_thw[0]).reshape(-1, 1, 1)
                        video_token_indices = np.broadcast_to(
                            video_token_indices, (video_token_indices.shape[0], height, width)
                        ).reshape(-1)
                        video_token_indices = (
                            video_token_indices * next(video_second_per_grid) * position_id_per_seconds
                        )

                        tokens_per_chunk = int(position_id_per_seconds * seconds_per_chunk)
                        video_chunk_indexes = self.get_chunked_index(video_token_indices, tokens_per_chunk)
                        audio_chunk_indexes = self.get_chunked_index(audio_token_indices, tokens_per_chunk)

                        placeholder_string = self.vision_bos_token + self.audio_bos_token
                        for j in range(max(len(video_chunk_indexes), len(audio_chunk_indexes))):
                            if j < len(video_chunk_indexes):
                                video_seq_length = video_chunk_indexes[j][1] - video_chunk_indexes[j][0]
                                placeholder_string += "<|video_placeholder|>" * video_seq_length
                            if j < len(audio_chunk_indexes):
                                audio_seq_length = audio_chunk_indexes[j][1] - audio_chunk_indexes[j][0]
                                placeholder_string += "<|audio_placeholder|>" * audio_seq_length
                        placeholder_string += self.audio_eos_token + self.vision_eos_token
                        sample = sample.replace(
                            self.vision_bos_token + self.video_token + self.vision_eos_token,
                            placeholder_string,
                            1,
                        )

            sample = sample.replace("<|audio_placeholder|>", self.audio_token)
            sample = sample.replace("<|image_placeholder|>", self.image_token)
            sample = sample.replace("<|video_placeholder|>", self.video_token)
            processed_text.append(sample)
        return processed_text