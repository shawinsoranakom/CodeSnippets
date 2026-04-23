def has_bom(fn):
    with fn.open("rb") as f:
        sample = f.read(4)
    return sample.startswith(
        (codecs.BOM_UTF8, codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)
    )