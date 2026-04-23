def django_check_file(filename, checkers, options=None):
    try:
        for checker in checkers:
            # Django docs use ".txt" for docs file extension.
            if ".rst" in checker.suffixes:
                checker.suffixes = (".txt",)
        ext = splitext(filename)[1]
        if not any(ext in checker.suffixes for checker in checkers):
            return Counter()
        try:
            with open(filename, encoding="utf-8") as f:
                text = f.read()
        except OSError as err:
            return [f"{filename}: cannot open: {err}"]
        except UnicodeDecodeError as err:
            return [f"{filename}: cannot decode as UTF-8: {err}"]
        return check_text(filename, text, checkers, options)
    finally:
        for memoized_function in PER_FILE_CACHES:
            memoized_function.cache_clear()