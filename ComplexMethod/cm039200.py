def load_files(
    container_path,
    *,
    description=None,
    categories=None,
    load_content=True,
    shuffle=True,
    encoding=None,
    decode_error="strict",
    random_state=0,
    allowed_extensions=None,
):
    """Load text files with categories as subfolder names.

    Individual samples are assumed to be files stored a two levels folder
    structure such as the following:

    .. code-block:: text

        container_folder/
            category_1_folder/
                file_1.txt
                file_2.txt
                ...
                file_42.txt
            category_2_folder/
                file_43.txt
                file_44.txt
                ...

    The folder names are used as supervised signal label names. The individual
    file names are not important.

    This function does not try to extract features into a numpy array or scipy
    sparse matrix. In addition, if load_content is false it does not try to
    load the files in memory.

    To use text files in a scikit-learn classification or clustering algorithm,
    you will need to use the :mod:`~sklearn.feature_extraction.text` module to
    build a feature extraction transformer that suits your problem.

    If you set load_content=True, you should also specify the encoding of the
    text using the 'encoding' parameter. For many modern text files, 'utf-8'
    will be the correct encoding. If you leave encoding equal to None, then the
    content will be made of bytes instead of Unicode, and you will not be able
    to use most functions in :mod:`~sklearn.feature_extraction.text`.

    Similar feature extractors should be built for other kind of unstructured
    data input such as images, audio, video, ...

    If you want files with a specific file extension (e.g. `.txt`) then you
    can pass a list of those file extensions to `allowed_extensions`.

    Read more in the :ref:`User Guide <datasets>`.

    Parameters
    ----------
    container_path : str
        Path to the main folder holding one subfolder per category.

    description : str, default=None
        A paragraph describing the characteristic of the dataset: its source,
        reference, etc.

    categories : list of str, default=None
        If None (default), load all the categories. If not None, list of
        category names to load (other categories ignored).

    load_content : bool, default=True
        Whether to load or not the content of the different files. If true a
        'data' attribute containing the text information is present in the data
        structure returned. If not, a filenames attribute gives the path to the
        files.

    shuffle : bool, default=True
        Whether or not to shuffle the data: might be important for models that
        make the assumption that the samples are independent and identically
        distributed (i.i.d.), such as stochastic gradient descent.

    encoding : str, default=None
        If None, do not try to decode the content of the files (e.g. for images
        or other non-text content). If not None, encoding to use to decode text
        files to Unicode if load_content is True.

    decode_error : {'strict', 'ignore', 'replace'}, default='strict'
        Instruction on what to do if a byte sequence is given to analyze that
        contains characters not of the given `encoding`. Passed as keyword
        argument 'errors' to bytes.decode.

    random_state : int, RandomState instance or None, default=0
        Determines random number generation for dataset shuffling. Pass an int
        for reproducible output across multiple function calls.
        See :term:`Glossary <random_state>`.

    allowed_extensions : list of str, default=None
        List of desired file extensions to filter the files to be loaded.

    Returns
    -------
    data : :class:`~sklearn.utils.Bunch`
        Dictionary-like object, with the following attributes.

        data : list of str
            Only present when `load_content=True`.
            The raw text data to learn.
        target : ndarray
            The target labels (integer index).
        target_names : list
            The names of target classes.
        DESCR : str
            The full description of the dataset.
        filenames: ndarray
            The filenames holding the dataset.

    Examples
    --------
    >>> from sklearn.datasets import load_files
    >>> container_path = "./"
    >>> load_files(container_path)  # doctest: +SKIP
    """

    target = []
    target_names = []
    filenames = []

    folders = [
        f for f in sorted(listdir(container_path)) if isdir(join(container_path, f))
    ]

    if categories is not None:
        folders = [f for f in folders if f in categories]

    if allowed_extensions is not None:
        allowed_extensions = frozenset(allowed_extensions)

    for label, folder in enumerate(folders):
        target_names.append(folder)
        folder_path = join(container_path, folder)
        files = sorted(listdir(folder_path))
        if allowed_extensions is not None:
            documents = [
                join(folder_path, file)
                for file in files
                if os.path.splitext(file)[1] in allowed_extensions
            ]
        else:
            documents = [join(folder_path, file) for file in files]
        target.extend(len(documents) * [label])
        filenames.extend(documents)

    # convert to array for fancy indexing
    filenames = np.array(filenames)
    target = np.array(target)

    if shuffle:
        random_state = check_random_state(random_state)
        indices = np.arange(filenames.shape[0])
        random_state.shuffle(indices)
        filenames = filenames[indices]
        target = target[indices]

    if load_content:
        data = []
        for filename in filenames:
            data.append(Path(filename).read_bytes())
        if encoding is not None:
            data = [d.decode(encoding, decode_error) for d in data]
        return Bunch(
            data=data,
            filenames=filenames,
            target_names=target_names,
            target=target,
            DESCR=description,
        )

    return Bunch(
        filenames=filenames, target_names=target_names, target=target, DESCR=description
    )