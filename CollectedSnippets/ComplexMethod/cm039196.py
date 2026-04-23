def _pandas_arff_parser(
    gzip_file,
    output_arrays_type,
    openml_columns_info,
    feature_names_to_select,
    target_names_to_select,
    read_csv_kwargs=None,
):
    """ARFF parser using `pandas.read_csv`.

    This parser uses the metadata fetched directly from OpenML and skips the metadata
    headers of ARFF file itself. The data is loaded as a CSV file.

    Parameters
    ----------
    gzip_file : GzipFile instance
        The GZip compressed file with the ARFF formatted payload.

    output_arrays_type : {"numpy", "sparse", "pandas"}
        The type of the arrays that will be returned. The possibilities are:

        - `"numpy"`: both `X` and `y` will be NumPy arrays;
        - `"sparse"`: `X` will be sparse matrix and `y` will be a NumPy array;
        - `"pandas"`: `X` will be a pandas DataFrame and `y` will be either a
          pandas Series or DataFrame.

    openml_columns_info : dict
        The information provided by OpenML regarding the columns of the ARFF
        file.

    feature_names_to_select : list of str
        A list of the feature names to be selected to build `X`.

    target_names_to_select : list of str
        A list of the target names to be selected to build `y`.

    read_csv_kwargs : dict, default=None
        Keyword arguments to pass to `pandas.read_csv`. It allows to overwrite
        the default options.

    Returns
    -------
    X : {ndarray, sparse matrix, dataframe}
        The data matrix.

    y : {ndarray, dataframe, series}
        The target.

    frame : dataframe or None
        A dataframe containing both `X` and `y`. `None` if
        `output_array_type != "pandas"`.

    categories : list of str or None
        The names of the features that are categorical. `None` if
        `output_array_type == "pandas"`.
    """
    import pandas as pd

    # read the file until the data section to skip the ARFF metadata headers
    for line in gzip_file:
        if line.decode("utf-8").lower().startswith("@data"):
            break

    dtypes = {}
    for name in openml_columns_info:
        column_dtype = openml_columns_info[name]["data_type"]
        if column_dtype.lower() == "integer":
            # Use Int64 to infer missing values from data
            # XXX: this line is not covered by our tests. Is this really needed?
            dtypes[name] = "Int64"
        elif column_dtype.lower() == "nominal":
            dtypes[name] = "category"
    # since we will not pass `names` when reading the ARFF file, we need to translate
    # `dtypes` from column names to column indices to pass to `pandas.read_csv`
    dtypes_positional = {
        col_idx: dtypes[name]
        for col_idx, name in enumerate(openml_columns_info)
        if name in dtypes
    }

    default_read_csv_kwargs = {
        "header": None,
        "index_col": False,  # always force pandas to not use the first column as index
        "na_values": ["?"],  # missing values are represented by `?`
        "keep_default_na": False,  # only `?` is a missing value given the ARFF specs
        "comment": "%",  # skip line starting by `%` since they are comments
        "quotechar": '"',  # delimiter to use for quoted strings
        "skipinitialspace": True,  # skip spaces after delimiter to follow ARFF specs
        "escapechar": "\\",
        "dtype": dtypes_positional,
    }
    read_csv_kwargs = {**default_read_csv_kwargs, **(read_csv_kwargs or {})}
    frame = pd.read_csv(gzip_file, **read_csv_kwargs)
    try:
        # Setting the columns while reading the file will select the N first columns
        # and not raise a ParserError. Instead, we set the columns after reading the
        # file and raise a ParserError if the number of columns does not match the
        # number of columns in the metadata given by OpenML.
        frame.columns = [name for name in openml_columns_info]
    except ValueError as exc:
        raise pd.errors.ParserError(
            "The number of columns provided by OpenML does not match the number of "
            "columns inferred by pandas when reading the file."
        ) from exc

    columns_to_select = feature_names_to_select + target_names_to_select
    columns_to_keep = [col for col in frame.columns if col in columns_to_select]
    frame = frame[columns_to_keep]

    # `pd.read_csv` automatically handles double quotes for quoting non-numeric
    # CSV cell values. Contrary to LIAC-ARFF, `pd.read_csv` cannot be configured to
    # consider either single quotes and double quotes as valid quoting chars at
    # the same time since this case does not occur in regular (non-ARFF) CSV files.
    # To mimic the behavior of LIAC-ARFF parser, we manually strip single quotes
    # on categories as a post-processing steps if needed.
    #
    # Note however that we intentionally do not attempt to do this kind of manual
    # post-processing of (non-categorical) string-typed columns because we cannot
    # resolve the ambiguity of the case of CSV cell with nesting quoting such as
    # `"'some string value'"` with pandas.
    single_quote_pattern = re.compile(r"^'(?P<contents>.*)'$")

    def strip_single_quotes(input_string):
        match = re.search(single_quote_pattern, input_string)
        if match is None:
            return input_string

        return match.group("contents")

    categorical_columns = [
        name
        for name, dtype in frame.dtypes.items()
        if isinstance(dtype, pd.CategoricalDtype)
    ]
    for col in categorical_columns:
        frame[col] = frame[col].cat.rename_categories(strip_single_quotes)

    X, y = _post_process_frame(frame, feature_names_to_select, target_names_to_select)

    if output_arrays_type == "pandas":
        return X, y, frame, None
    else:
        X, y = X.to_numpy(), y.to_numpy()

    categories = {
        name: dtype.categories.tolist()
        for name, dtype in frame.dtypes.items()
        if isinstance(dtype, pd.CategoricalDtype)
    }
    return X, y, None, categories