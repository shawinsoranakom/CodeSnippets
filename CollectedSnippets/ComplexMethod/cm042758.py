def preprocess_speaker(speaker_dir, out_dir: Path, skip_existing: bool, hparams, no_alignments: bool):
    metadata = []
    for book_dir in speaker_dir.glob("*"):
        if no_alignments:
            # Gather the utterance audios and texts
            # LibriTTS uses .wav but we will include extensions for compatibility with other datasets
            extensions = ["*.wav", "*.flac", "*.mp3"]
            for extension in extensions:
                wav_fpaths = book_dir.glob(extension)

                for wav_fpath in wav_fpaths:
                    # Load the audio waveform
                    wav, _ = librosa.load(str(wav_fpath), hparams.sample_rate)
                    if hparams.rescale:
                        wav = wav / np.abs(wav).max() * hparams.rescaling_max

                    # Get the corresponding text
                    # Check for .txt (for compatibility with other datasets)
                    text_fpath = wav_fpath.with_suffix(".txt")
                    if not text_fpath.exists():
                        # Check for .normalized.txt (LibriTTS)
                        text_fpath = wav_fpath.with_suffix(".normalized.txt")
                        assert text_fpath.exists()
                    with text_fpath.open("r") as text_file:
                        text = "".join([line for line in text_file])
                        text = text.replace("\"", "")
                        text = text.strip()

                    # Process the utterance
                    metadata.append(process_utterance(wav, text, out_dir, str(wav_fpath.with_suffix("").name),
                                                      skip_existing, hparams))
        else:
            # Process alignment file (LibriSpeech support)
            # Gather the utterance audios and texts
            try:
                alignments_fpath = next(book_dir.glob("*.alignment.txt"))
                with alignments_fpath.open("r") as alignments_file:
                    alignments = [line.rstrip().split(" ") for line in alignments_file]
            except StopIteration:
                # A few alignment files will be missing
                continue

            # Iterate over each entry in the alignments file
            for wav_fname, words, end_times in alignments:
                wav_fpath = book_dir.joinpath(wav_fname + ".flac")
                assert wav_fpath.exists()
                words = words.replace("\"", "").split(",")
                end_times = list(map(float, end_times.replace("\"", "").split(",")))

                # Process each sub-utterance
                wavs, texts = split_on_silences(wav_fpath, words, end_times, hparams)
                for i, (wav, text) in enumerate(zip(wavs, texts)):
                    sub_basename = "%s_%02d" % (wav_fname, i)
                    metadata.append(process_utterance(wav, text, out_dir, sub_basename,
                                                      skip_existing, hparams))

    return [m for m in metadata if m is not None]