def _marshall_index(pandas_index, proto_index) -> None:
    """Convert an pandas.Index into a proto.Index.

    pandas_index - Panda.Index or related (input)
    proto_index  - proto.Index (output)
    """
    import numpy as np
    import pandas as pd

    if type(pandas_index) == pd.Index:
        _marshall_any_array(np.array(pandas_index), proto_index.plain_index.data)
    elif type(pandas_index) == pd.RangeIndex:
        min = pandas_index.min()
        max = pandas_index.max()
        if pd.isna(min) or pd.isna(max):
            proto_index.range_index.start = 0
            proto_index.range_index.stop = 0
        else:
            proto_index.range_index.start = min
            proto_index.range_index.stop = max + 1
    elif type(pandas_index) == pd.MultiIndex:
        for level in pandas_index.levels:
            _marshall_index(level, proto_index.multi_index.levels.add())
        if hasattr(pandas_index, "codes"):
            index_codes = pandas_index.codes
        else:
            # Deprecated in Pandas 0.24, do don't bother covering.
            index_codes = pandas_index.labels  # pragma: no cover
        for label in index_codes:
            proto_index.multi_index.labels.add().data.extend(label)
    elif type(pandas_index) == pd.DatetimeIndex:
        if pandas_index.tz is None:
            current_zone = tzlocal.get_localzone()
            pandas_index = pandas_index.tz_localize(current_zone)
        proto_index.datetime_index.data.data.extend(
            pandas_index.map(datetime.datetime.isoformat)
        )
    elif type(pandas_index) == pd.TimedeltaIndex:
        proto_index.timedelta_index.data.data.extend(pandas_index.astype(np.int64))
    elif type(pandas_index) == pd.Int64Index:
        proto_index.int_64_index.data.data.extend(pandas_index)
    elif type(pandas_index) == pd.Float64Index:
        proto_index.float_64_index.data.data.extend(pandas_index)
    else:
        raise NotImplementedError("Can't handle %s yet." % type(pandas_index))