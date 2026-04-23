def get_dataset_filelist(a):
    training_files = []
    validation_files = []
    list_unseen_validation_files = []

    with open(a.input_training_file, "r", encoding="utf-8") as fi:
        training_files = [
            os.path.join(a.input_wavs_dir, x.split("|")[0] + ".wav") for x in fi.read().split("\n") if len(x) > 0
        ]
        print(f"first training file: {training_files[0]}")

    with open(a.input_validation_file, "r", encoding="utf-8") as fi:
        validation_files = [
            os.path.join(a.input_wavs_dir, x.split("|")[0] + ".wav") for x in fi.read().split("\n") if len(x) > 0
        ]
        print(f"first validation file: {validation_files[0]}")

    for i in range(len(a.list_input_unseen_validation_file)):
        with open(a.list_input_unseen_validation_file[i], "r", encoding="utf-8") as fi:
            unseen_validation_files = [
                os.path.join(a.list_input_unseen_wavs_dir[i], x.split("|")[0] + ".wav")
                for x in fi.read().split("\n")
                if len(x) > 0
            ]
            print(f"first unseen {i}th validation fileset: {unseen_validation_files[0]}")
            list_unseen_validation_files.append(unseen_validation_files)

    return training_files, validation_files, list_unseen_validation_files