def _get_audios_and_audio_lengths(self, audios: AudioInput) -> Sequence["torch.Tensor", Sequence[int]]:
        """
        Coerces audio inputs to torch tensors and extracts audio lengths prior to stacking.

        Args:
            audios (`AudioInput`):
                Audio sequence, numpy array, or torch tensor.
        """
        requires_backends(self, ["torch"])

        # Coerce to PyTorch tensors if we have numpy arrays, since
        # currently we have a dependency on torch/torchaudio anyway
        if isinstance(audios, np.ndarray):
            audios = torch.from_numpy(audios)
        elif isinstance(audios, Sequence) and isinstance(audios[0], np.ndarray):
            audios = [torch.from_numpy(arr) for arr in audios]

        if isinstance(audios, torch.Tensor):
            if audios.ndim == 1:
                audios = audios.unsqueeze(0)
            if not torch.is_floating_point(audios):
                raise ValueError("Invalid audio provided. Audio should be a floating point between 0 and 1")

            if audios.shape[0] > 1:
                logger.warning("Audio samples are already collated; assuming they all have the same length")
            lengths = [audios.shape[-1]] * audios.shape[0]
            return audios, lengths

        elif isinstance(audios, Sequence) and isinstance(audios[0], torch.Tensor):
            if not torch.is_floating_point(audios[0]):
                raise ValueError("Invalid audio provided. Audio should be a floating point between 0 and 1")
            lengths = [audio.shape[-1] for audio in audios]
            audios = [audio.squeeze(0) for audio in audios]
            audios = torch.nn.utils.rnn.pad_sequence(audios, batch_first=True, padding_value=0.0)
            return audios, lengths

        raise TypeError("Invalid audio provided. Audio should be a one or more torch tensors or numpy arrays")