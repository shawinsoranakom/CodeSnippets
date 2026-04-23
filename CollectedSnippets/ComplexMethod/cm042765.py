def __init__(self, metadata_fpath: Path, mel_dir: Path, wav_dir: Path):
        print("Using inputs from:\n\t%s\n\t%s\n\t%s" % (metadata_fpath, mel_dir, wav_dir))

        with metadata_fpath.open("r") as metadata_file:
            metadata = [line.split("|") for line in metadata_file]

        gta_fnames = [x[1] for x in metadata if int(x[4])]
        gta_fpaths = [mel_dir.joinpath(fname) for fname in gta_fnames]
        wav_fnames = [x[0] for x in metadata if int(x[4])]
        wav_fpaths = [wav_dir.joinpath(fname) for fname in wav_fnames]
        self.samples_fpaths = list(zip(gta_fpaths, wav_fpaths))

        print("Found %d samples" % len(self.samples_fpaths))