def findtests(*, testdir: StrPath | None = None, exclude: Container[str] = (),
              split_test_dirs: set[TestName] = SPLITTESTDIRS,
              base_mod: str = "") -> TestList:
    """Return a list of all applicable test modules."""
    testdir = findtestdir(testdir)
    tests = []
    for name in os.listdir(testdir):
        mod, ext = os.path.splitext(name)
        if (not mod.startswith("test_")) or (mod in exclude):
            continue
        if base_mod:
            fullname = f"{base_mod}.{mod}"
        else:
            fullname = mod
        if fullname in split_test_dirs:
            subdir = os.path.join(testdir, mod)
            if not base_mod:
                fullname = f"test.{mod}"
            tests.extend(findtests(testdir=subdir, exclude=exclude,
                                   split_test_dirs=split_test_dirs,
                                   base_mod=fullname))
        elif ext in (".py", ""):
            tests.append(fullname)
    return sorted(tests)