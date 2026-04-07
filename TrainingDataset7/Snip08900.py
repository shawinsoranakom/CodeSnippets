def ignore(pattern):
        return fnmatch.fnmatchcase(path.name, pattern) or fnmatch.fnmatchcase(
            str(path), pattern
        )