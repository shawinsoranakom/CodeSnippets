def index_directory(
    directory,
    labels,
    formats,
    class_names=None,
    shuffle=True,
    seed=None,
    follow_links=False,
    verbose=True,
):
    """List all files in `directory`, with their labels.

    Args:
        directory: Directory where the data is located.
            If `labels` is `"inferred"`, it should contain
            subdirectories, each containing files for a class.
            Otherwise, the directory structure is ignored.
        labels: Either `"inferred"`
            (labels are generated from the directory structure),
            `None` (no labels),
            or a list/tuple of integer labels of the same size as the number
            of valid files found in the directory.
            Labels should be sorted according
            to the alphanumeric order of the image file paths
            (obtained via `os.walk(directory)` in Python).
        formats: Allowlist of file extensions to index
            (e.g. `".jpg"`, `".txt"`).
        class_names: Only valid if `labels="inferred"`. This is the explicit
            list of class names (must match names of subdirectories). Used
            to control the order of the classes
            (otherwise alphanumerical order is used).
        shuffle: Whether to shuffle the data. Defaults to `True`.
            If set to `False`, sorts the data in alphanumeric order.
        seed: Optional random seed for shuffling.
        follow_links: Whether to visits subdirectories pointed to by symlinks.
        verbose: Whether the function prints number of files found and classes.
            Defaults to `True`.

    Returns:
        tuple (file_paths, labels, class_names).
        - file_paths: list of file paths (strings).
        - labels: list of matching integer labels (same length as file_paths)
        - class_names: names of the classes corresponding to these labels, in
        order.
    """
    if file_utils.is_remote_path(directory):
        from keras.src.utils.module_utils import tensorflow as tf

        os_module = tf.io.gfile
        path_module = tf.io.gfile
    else:
        os_module = os
        path_module = os.path

    if labels == "inferred":
        subdirs = []
        for subdir in sorted(os_module.listdir(directory)):
            if path_module.isdir(path_module.join(directory, subdir)):
                if not subdir.startswith("."):
                    if subdir.endswith("/"):
                        subdir = subdir[:-1]
                    subdirs.append(subdir)
        if class_names is not None:
            if not set(class_names).issubset(set(subdirs)):
                raise ValueError(
                    "The `class_names` passed did not match the "
                    "names of the subdirectories of the target directory. "
                    f"Expected: {subdirs} (or a subset of it), "
                    f"but received: class_names={class_names}"
                )
            subdirs = class_names  # Keep provided order.
    else:
        # In the explicit/no-label cases, index from the parent directory down.
        subdirs = [""]
        if class_names is not None:
            if labels is None:
                raise ValueError(
                    "When `labels=None` (no labels), argument `class_names` "
                    "cannot be specified."
                )
            else:
                raise ValueError(
                    "When argument `labels` is specified, argument "
                    "`class_names` cannot be specified (the `class_names` "
                    "will be the sorted list of labels)."
                )
    class_names = subdirs
    class_indices = dict(zip(class_names, range(len(class_names))))

    # Build an index of the files
    # in the different class subfolders.
    pool = ThreadPool()
    results = []
    filenames = []

    for dirpath in (path_module.join(directory, subdir) for subdir in subdirs):
        results.append(
            pool.apply_async(
                index_subdirectory,
                (dirpath, class_indices, follow_links, formats),
            )
        )
    labels_list = []
    for res in results:
        partial_filenames, partial_labels = res.get()
        labels_list.append(partial_labels)
        filenames += partial_filenames

    if labels == "inferred":
        # Inferred labels.
        i = 0
        labels = np.zeros((len(filenames),), dtype="int32")
        for partial_labels in labels_list:
            labels[i : i + len(partial_labels)] = partial_labels
            i += len(partial_labels)
    elif labels is None:
        class_names = None
    else:
        # Manual labels.
        if len(labels) != len(filenames):
            raise ValueError(
                "Expected the lengths of `labels` to match the number "
                "of files in the target directory. len(labels) is "
                f"{len(labels)} while we found {len(filenames)} files "
                f"in directory {directory}."
            )
        class_names = [str(label) for label in sorted(set(labels))]
    if verbose:
        if labels is None:
            io_utils.print_msg(f"Found {len(filenames)} files.")
        else:
            io_utils.print_msg(
                f"Found {len(filenames)} files belonging "
                f"to {len(class_names)} classes."
            )
    pool.close()
    pool.join()
    file_paths = [path_module.join(directory, fname) for fname in filenames]

    if shuffle:
        # Shuffle globally to erase macro-structure
        if seed is None:
            seed = np.random.randint(1e6)
        rng = np.random.RandomState(seed)
        rng.shuffle(file_paths)
        if labels is not None:
            rng = np.random.RandomState(seed)
            rng.shuffle(labels)
    return file_paths, labels, class_names