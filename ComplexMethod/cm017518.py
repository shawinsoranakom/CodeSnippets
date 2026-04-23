def __init__(self, *expressions, length=None, columns=(), **kwargs):
        super().__init__(*expressions, **kwargs)
        if len(self.fields) > 32:
            raise ValueError("Bloom indexes support a maximum of 32 fields.")
        if not isinstance(columns, (list, tuple)):
            raise ValueError("BloomIndex.columns must be a list or tuple.")
        if len(columns) > len(self.fields):
            raise ValueError("BloomIndex.columns cannot have more values than fields.")
        if not all(0 < col <= 4095 for col in columns):
            raise ValueError(
                "BloomIndex.columns must contain integers from 1 to 4095.",
            )
        if length is not None and not 0 < length <= 4096:
            raise ValueError(
                "BloomIndex.length must be None or an integer from 1 to 4096.",
            )
        self.length = length
        self.columns = columns