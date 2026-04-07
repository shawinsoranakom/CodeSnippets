def garbage_collect():
    gc.collect()
    if PYPY:
        # Collecting weakreferences can take two collections on PyPy.
        gc.collect()