async def get_input_stream(self) -> AsyncGenerator[StreamingInput]:
        for frame_size, num_tokens in self._generate_frame_size_and_num_tokens():
            next_tokens = [await self._token_queue.get() for _ in range(num_tokens)]

            audio_arrays: list[np.ndarray] = (
                [self._leftover] if self._leftover is not None else []
            )
            while sum(len(arr) for arr in audio_arrays) < frame_size:
                arr = await self._audio_queue.get()
                if arr is None:
                    return
                audio_arrays.append(arr)

            audio_array = np.concatenate(audio_arrays)
            frame = audio_array[:frame_size]

            # The current stride took look_ahead_in_samples audio of the next sample
            # In addition the next sample will take look_back_in_samples audio of
            # the current sample => So let's put both of this into the leftover
            stride = (
                frame_size - self._look_ahead_in_samples - self._look_back_in_samples
            )
            assert stride > 0, f"{stride=} must be positive"

            self._leftover = audio_array[stride:]

            yield StreamingInput(
                TokensPrompt(
                    prompt_token_ids=next_tokens,
                    multi_modal_data={"audio": (frame, None)},
                )
            )