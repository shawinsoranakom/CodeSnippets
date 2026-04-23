def save_audio(
        self,
        audio: AudioInput,
        saving_path: str | Path | list[str | Path],
        **kwargs: Unpack[HiggsAudioV2ProcessorKwargs],
    ):
        # TODO: @eustlb, this should be in AudioProcessor
        if not is_soundfile_available():
            raise ImportError("Please install `soundfile` to save audio files.")

        # ensure correct audio input
        audio = make_list_of_audio(audio)

        # ensure correct saving path
        if isinstance(saving_path, (str, Path)):
            saving_path = [saving_path]
        elif not (isinstance(saving_path, (list, tuple)) and all(isinstance(p, (str, Path)) for p in saving_path)):
            raise ValueError("Invalid input path. Please provide a string, or a list of strings")

        if len(audio) != len(saving_path):
            raise ValueError("The number of audio and saving paths must be the same")

        output_kwargs = self._merge_kwargs(
            HiggsAudioV2ProcessorKwargs,
            **kwargs,
        )
        audio_kwargs = output_kwargs["audio_kwargs"]
        sampling_rate = audio_kwargs["sampling_rate"]

        for audio_value, p in zip(audio, saving_path):
            if isinstance(audio_value, torch.Tensor):
                audio_value = audio_value.cpu().float().numpy()
            sf.write(p, audio_value, sampling_rate)