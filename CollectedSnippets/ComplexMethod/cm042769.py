def preprocess_voxceleb1(datasets_root: Path, out_dir: Path, skip_existing=False):
    # Initialize the preprocessing
    dataset_name = "VoxCeleb1"
    dataset_root, logger = _init_preprocess_dataset(dataset_name, datasets_root, out_dir)
    if not dataset_root:
        return

    # Get the contents of the meta file
    with dataset_root.joinpath("vox1_meta.csv").open("r") as metafile:
        metadata = [line.split("\t") for line in metafile][1:]

    # Select the ID and the nationality, filter out non-anglophone speakers
    nationalities = {line[0]: line[3] for line in metadata}
    keep_speaker_ids = [speaker_id for speaker_id, nationality in nationalities.items() if
                        nationality.lower() in anglophone_nationalites]
    print("VoxCeleb1: using samples from %d (presumed anglophone) speakers out of %d." %
          (len(keep_speaker_ids), len(nationalities)))

    # Get the speaker directories for anglophone speakers only
    speaker_dirs = dataset_root.joinpath("wav").glob("*")
    speaker_dirs = [speaker_dir for speaker_dir in speaker_dirs if
                    speaker_dir.name in keep_speaker_ids]
    print("VoxCeleb1: found %d anglophone speakers on the disk, %d missing (this is normal)." %
          (len(speaker_dirs), len(keep_speaker_ids) - len(speaker_dirs)))

    # Preprocess all speakers
    _preprocess_speaker_dirs(speaker_dirs, dataset_name, datasets_root, out_dir, skip_existing, logger)