def _fetch_lfw_pairs(
    index_file_path, data_folder_path, slice_=None, color=False, resize=None
):
    """Perform the actual data loading for the LFW pairs dataset

    This operation is meant to be cached by a joblib wrapper.
    """
    # parse the index file to find the number of pairs to be able to allocate
    # the right amount of memory before starting to decode the jpeg files
    with open(index_file_path, "rb") as index_file:
        split_lines = [ln.decode().strip().split("\t") for ln in index_file]
    pair_specs = [sl for sl in split_lines if len(sl) > 2]
    n_pairs = len(pair_specs)

    # iterating over the metadata lines for each pair to find the filename to
    # decode and load in memory
    target = np.zeros(n_pairs, dtype=int)
    file_paths = list()
    for i, components in enumerate(pair_specs):
        if len(components) == 3:
            target[i] = 1
            pair = (
                (components[0], int(components[1]) - 1),
                (components[0], int(components[2]) - 1),
            )
        elif len(components) == 4:
            target[i] = 0
            pair = (
                (components[0], int(components[1]) - 1),
                (components[2], int(components[3]) - 1),
            )
        else:
            raise ValueError("invalid line %d: %r" % (i + 1, components))
        for j, (name, idx) in enumerate(pair):
            try:
                person_folder = join(data_folder_path, name)
            except TypeError:
                person_folder = join(data_folder_path, str(name, "UTF-8"))
            filenames = list(sorted(listdir(person_folder)))
            file_path = join(person_folder, filenames[idx])
            file_paths.append(file_path)

    pairs = _load_imgs(file_paths, slice_, color, resize)
    shape = list(pairs.shape)
    n_faces = shape.pop(0)
    shape.insert(0, 2)
    shape.insert(0, n_faces // 2)
    pairs.shape = shape

    return pairs, target, np.array(["Different persons", "Same person"])