def __iter__(self):
        yield from formats.get_format("DATETIME_INPUT_FORMATS")
        yield from formats.get_format("DATE_INPUT_FORMATS")