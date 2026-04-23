def read_refcount_data(refcount_filename: Path) -> dict[str, RefCountEntry]:
    refcount_data = {}
    refcounts = refcount_filename.read_text(encoding="utf8")
    for line in refcounts.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            # blank lines and comments
            continue

        # Each line is of the form
        # function ':' type ':' [param name] ':' [refcount effect] ':' [comment]
        parts = line.split(":", 4)
        if len(parts) != 5:
            raise ValueError(f"Wrong field count in {line!r}")
        function, type, arg, refcount, _comment = parts

        # Get the entry, creating it if needed:
        try:
            entry = refcount_data[function]
        except KeyError:
            entry = refcount_data[function] = RefCountEntry(function)
        if not refcount or refcount == "null":
            refcount = None
        else:
            refcount = int(refcount)
        # Update the entry with the new parameter
        # or the result information.
        if arg:
            entry.args.append((arg, type, refcount))
        else:
            entry.result_type = type
            entry.result_refs = refcount

    return refcount_data