def sanitize_strftime_format(fmt):
    """
    Ensure that certain specifiers are correctly padded with leading zeros.

    For years < 1000 specifiers %C, %F, %G, and %Y don't work as expected for
    strftime provided by glibc on Linux as they don't pad the year or century
    with leading zeros. Support for specifying the padding explicitly is
    available, however, which can be used to fix this issue.

    FreeBSD, macOS, and Windows do not support explicitly specifying the
    padding, but return four digit years (with leading zeros) as expected.

    This function checks whether the %Y produces a correctly padded string and,
    if not, makes the following substitutions:

    - %C → %02C
    - %F → %010F
    - %G → %04G
    - %Y → %04Y

    See https://bugs.python.org/issue13305 for more details.
    """
    if datetime.date(1, 1, 1).strftime("%Y") == "0001":
        return fmt
    mapping = {"C": 2, "F": 10, "G": 4, "Y": 4}
    return re.sub(
        r"((?:^|[^%])(?:%%)*)%([CFGY])",
        lambda m: r"%s%%0%s%s" % (m[1], mapping[m[2]], m[2]),
        fmt,
    )