def _convert_data_format(data_format, ndim):
    if data_format == "channels_last":
        if ndim == 3:
            return "NWC"
        elif ndim == 4:
            return "NHWC"
        elif ndim == 5:
            return "NDHWC"
        else:
            raise ValueError(
                f"Input rank not supported: {ndim}. "
                "Expected values are [3, 4, 5]"
            )
    elif data_format == "channels_first":
        if ndim == 3:
            return "NCW"
        elif ndim == 4:
            return "NCHW"
        elif ndim == 5:
            return "NCDHW"
        else:
            raise ValueError(
                f"Input rank not supported: {ndim}. "
                "Expected values are [3, 4, 5]"
            )
    else:
        raise ValueError(
            f"Invalid data_format: {data_format}. "
            'Expected values are ["channels_first", "channels_last"]'
        )