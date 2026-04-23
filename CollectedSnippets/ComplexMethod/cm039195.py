def _liac_arff_parser(
    gzip_file,
    output_arrays_type,
    openml_columns_info,
    feature_names_to_select,
    target_names_to_select,
    shape=None,
):
    """ARFF parser using the LIAC-ARFF library coded purely in Python.

    This parser is quite slow but consumes a generator. Currently it is needed
    to parse sparse datasets. For dense datasets, it is recommended to instead
    use the pandas-based parser, although it does not always handles the
    dtypes exactly the same.

    Parameters
    ----------
    gzip_file : GzipFile instance
        The file compressed to be read.

    output_arrays_type : {"numpy", "sparse", "pandas"}
        The type of the arrays that will be returned. The possibilities ara:

        - `"numpy"`: both `X` and `y` will be NumPy arrays;
        - `"sparse"`: `X` will be sparse matrix and `y` will be a NumPy array;
        - `"pandas"`: `X` will be a pandas DataFrame and `y` will be either a
          pandas Series or DataFrame.

    columns_info : dict
        The information provided by OpenML regarding the columns of the ARFF
        file.

    feature_names_to_select : list of str
        A list of the feature names to be selected.

    target_names_to_select : list of str
        A list of the target names to be selected.

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

    def _io_to_generator(gzip_file):
        for line in gzip_file:
            yield line.decode("utf-8")

    stream = _io_to_generator(gzip_file)

    # find which type (dense or sparse) ARFF type we will have to deal with
    return_type = _arff.COO if output_arrays_type == "sparse" else _arff.DENSE_GEN
    # we should not let LIAC-ARFF to encode the nominal attributes with NumPy
    # arrays to have only numerical values.
    encode_nominal = not (output_arrays_type == "pandas")
    arff_container = _arff.load(
        stream, return_type=return_type, encode_nominal=encode_nominal
    )
    columns_to_select = feature_names_to_select + target_names_to_select

    categories = {
        name: cat
        for name, cat in arff_container["attributes"]
        if isinstance(cat, list) and name in columns_to_select
    }
    if output_arrays_type == "pandas":
        pd = check_pandas_support("fetch_openml with as_frame=True")

        columns_info = OrderedDict(arff_container["attributes"])
        columns_names = list(columns_info.keys())

        # calculate chunksize
        first_row = next(arff_container["data"])
        first_df = pd.DataFrame([first_row], columns=columns_names, copy=False)

        row_bytes = first_df.memory_usage(deep=True).sum()
        chunksize = get_chunk_n_rows(row_bytes)

        # read arff data with chunks
        columns_to_keep = [col for col in columns_names if col in columns_to_select]
        dfs = [first_df[columns_to_keep]]
        for data in chunk_generator(arff_container["data"], chunksize):
            dfs.append(
                pd.DataFrame(data, columns=columns_names, copy=False)[columns_to_keep]
            )
        # dfs[0] contains only one row, which may not have enough data to infer to
        # column's dtype. Here we use `dfs[1]` to configure the dtype in dfs[0]
        if len(dfs) >= 2:
            dfs[0] = dfs[0].astype(dfs[1].dtypes)

        # liac-arff parser does not depend on NumPy and uses None to represent
        # missing values. To be consistent with the pandas parser, we replace
        # None with np.nan.
        frame = pd.concat(dfs, ignore_index=True)
        frame = pd_fillna(pd, frame)
        del dfs, first_df

        # cast the columns frame
        dtypes = {}
        for name in frame.columns:
            column_dtype = openml_columns_info[name]["data_type"]
            if column_dtype.lower() == "integer":
                # Use a pandas extension array instead of np.int64 to be able
                # to support missing values.
                dtypes[name] = "Int64"
            elif column_dtype.lower() == "nominal":
                dtypes[name] = "category"
            else:
                dtypes[name] = frame.dtypes[name]
        frame = frame.astype(dtypes)

        X, y = _post_process_frame(
            frame, feature_names_to_select, target_names_to_select
        )
    else:
        arff_data = arff_container["data"]

        feature_indices_to_select = [
            int(openml_columns_info[col_name]["index"])
            for col_name in feature_names_to_select
        ]
        target_indices_to_select = [
            int(openml_columns_info[col_name]["index"])
            for col_name in target_names_to_select
        ]

        if isinstance(arff_data, Generator):
            if shape is None:
                raise ValueError(
                    "shape must be provided when arr['data'] is a Generator"
                )
            if shape[0] == -1:
                count = -1
            else:
                count = shape[0] * shape[1]
            data = np.fromiter(
                itertools.chain.from_iterable(arff_data),
                dtype="float64",
                count=count,
            )
            data = data.reshape(*shape)
            X = data[:, feature_indices_to_select]
            y = data[:, target_indices_to_select]
        elif isinstance(arff_data, tuple):
            arff_data_X = _split_sparse_columns(arff_data, feature_indices_to_select)
            num_obs = max(arff_data[1]) + 1
            X_shape = (num_obs, len(feature_indices_to_select))
            X = sp.sparse.coo_array(
                (arff_data_X[0], (arff_data_X[1], arff_data_X[2])),
                shape=X_shape,
                dtype=np.float64,
            )
            X = _align_api_if_sparse(X.tocsr())
            y = _sparse_data_to_array(arff_data, target_indices_to_select)
        else:
            # This should never happen
            raise ValueError(
                f"Unexpected type for data obtained from arff: {type(arff_data)}"
            )

        is_classification = {
            col_name in categories for col_name in target_names_to_select
        }
        if not is_classification:
            # No target
            pass
        elif all(is_classification):
            y = np.hstack(
                [
                    np.take(
                        np.asarray(categories.pop(col_name), dtype="O"),
                        y[:, i : i + 1].astype(int, copy=False),
                    )
                    for i, col_name in enumerate(target_names_to_select)
                ]
            )
        elif any(is_classification):
            raise ValueError(
                "Mix of nominal and non-nominal targets is not currently supported"
            )

        # reshape y back to 1-D array, if there is only 1 target column;
        # back to None if there are not target columns
        if y.shape[1] == 1:
            y = y.reshape((-1,))
        elif y.shape[1] == 0:
            y = None

    if output_arrays_type == "pandas":
        return X, y, frame, None
    return X, y, None, categories