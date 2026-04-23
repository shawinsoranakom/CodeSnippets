def collate_synthesizer(batch, r, hparams):
    # Text
    x_lens = [len(x[0]) for x in batch]
    max_x_len = max(x_lens)

    chars = [pad1d(x[0], max_x_len) for x in batch]
    chars = np.stack(chars)

    # Mel spectrogram
    spec_lens = [x[1].shape[-1] for x in batch]
    max_spec_len = max(spec_lens) + 1 
    if max_spec_len % r != 0:
        max_spec_len += r - max_spec_len % r 

    # WaveRNN mel spectrograms are normalized to [0, 1] so zero padding adds silence
    # By default, SV2TTS uses symmetric mels, where -1*max_abs_value is silence.
    if hparams.symmetric_mels:
        mel_pad_value = -1 * hparams.max_abs_value
    else:
        mel_pad_value = 0

    mel = [pad2d(x[1], max_spec_len, pad_value=mel_pad_value) for x in batch]
    mel = np.stack(mel)

    # Speaker embedding (SV2TTS)
    embeds = np.array([x[2] for x in batch])

    # Index (for vocoder preprocessing)
    indices = [x[3] for x in batch]


    # Convert all to tensor
    chars = torch.tensor(chars).long()
    mel = torch.tensor(mel)
    embeds = torch.tensor(embeds)

    return chars, mel, embeds, indices