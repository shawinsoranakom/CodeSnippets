def execute(cls, audio1, audio2, merge_method) -> IO.NodeOutput:
        waveform_1 = audio1["waveform"]
        waveform_2 = audio2["waveform"]
        sample_rate_1 = audio1["sample_rate"]
        sample_rate_2 = audio2["sample_rate"]

        waveform_1, waveform_2, output_sample_rate = match_audio_sample_rates(waveform_1, sample_rate_1, waveform_2, sample_rate_2)

        length_1 = waveform_1.shape[-1]
        length_2 = waveform_2.shape[-1]

        if length_2 > length_1:
            logging.info(f"AudioMerge: Trimming audio2 from {length_2} to {length_1} samples to match audio1 length.")
            waveform_2 = waveform_2[..., :length_1]
        elif length_2 < length_1:
            logging.info(f"AudioMerge: Padding audio2 from {length_2} to {length_1} samples to match audio1 length.")
            pad_shape = list(waveform_2.shape)
            pad_shape[-1] = length_1 - length_2
            pad_tensor = torch.zeros(pad_shape, dtype=waveform_2.dtype, device=waveform_2.device)
            waveform_2 = torch.cat((waveform_2, pad_tensor), dim=-1)

        if merge_method == "add":
            waveform = waveform_1 + waveform_2
        elif merge_method == "subtract":
            waveform = waveform_1 - waveform_2
        elif merge_method == "multiply":
            waveform = waveform_1 * waveform_2
        elif merge_method == "mean":
            waveform = (waveform_1 + waveform_2) / 2

        max_val = waveform.abs().max()
        if max_val > 1.0:
            waveform = waveform / max_val

        return IO.NodeOutput({"waveform": waveform, "sample_rate": output_sample_rate})