def __init__(self, metadata_fpath: Path, mel_dir: Path, embed_dir: Path, hparams):
        print("Using inputs from:\n\t%s\n\t%s\n\t%s" % (metadata_fpath, mel_dir, embed_dir))

        with metadata_fpath.open("r") as metadata_file:
            metadata = [line.split("|") for line in metadata_file]

        mel_fnames = [x[1] for x in metadata if int(x[4])]
        mel_fpaths = [mel_dir.joinpath(fname) for fname in mel_fnames]
        embed_fnames = [x[2] for x in metadata if int(x[4])]
        embed_fpaths = [embed_dir.joinpath(fname) for fname in embed_fnames]
        self.samples_fpaths = list(zip(mel_fpaths, embed_fpaths))
        self.samples_texts = [x[5].strip() for x in metadata if int(x[4])]
        self.metadata = metadata
        self.hparams = hparams

        print("Found %d samples" % len(self.samples_fpaths))