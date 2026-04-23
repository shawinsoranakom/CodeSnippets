def _preprocess_speaker(speaker_dir: Path, datasets_root: Path, out_dir: Path, skip_existing: bool):
    # Give a name to the speaker that includes its dataset
    speaker_name = "_".join(speaker_dir.relative_to(datasets_root).parts)

    # Create an output directory with that name, as well as a txt file containing a
    # reference to each source file.
    speaker_out_dir = out_dir.joinpath(speaker_name)
    speaker_out_dir.mkdir(exist_ok=True)
    sources_fpath = speaker_out_dir.joinpath("_sources.txt")

    # There's a possibility that the preprocessing was interrupted earlier, check if
    # there already is a sources file.
    if sources_fpath.exists():
        try:
            with sources_fpath.open("r") as sources_file:
                existing_fnames = {line.split(",")[0] for line in sources_file}
        except:
            existing_fnames = {}
    else:
        existing_fnames = {}

    # Gather all audio files for that speaker recursively
    sources_file = sources_fpath.open("a" if skip_existing else "w")
    audio_durs = []
    for extension in _AUDIO_EXTENSIONS:
        for in_fpath in speaker_dir.glob("**/*.%s" % extension):
            # Check if the target output file already exists
            out_fname = "_".join(in_fpath.relative_to(speaker_dir).parts)
            out_fname = out_fname.replace(".%s" % extension, ".npy")
            if skip_existing and out_fname in existing_fnames:
                continue

            # Load and preprocess the waveform
            wav = audio.preprocess_wav(in_fpath)
            if len(wav) == 0:
                continue

            # Create the mel spectrogram, discard those that are too short
            frames = audio.wav_to_mel_spectrogram(wav)
            if len(frames) < partials_n_frames:
                continue

            out_fpath = speaker_out_dir.joinpath(out_fname)
            np.save(out_fpath, frames)
            sources_file.write("%s,%s\n" % (out_fname, in_fpath))
            audio_durs.append(len(wav) / sampling_rate)

    sources_file.close()

    return audio_durs