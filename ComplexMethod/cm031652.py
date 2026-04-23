def main():
    base_branch = get_base_branch()
    file_paths = changed_files(base_branch)
    has_doc_files = any(fn for fn in file_paths if fn.startswith('Doc') and
                        fn.endswith(('.rst', '.inc')))
    misc_files = {p for p in file_paths if p.startswith('Misc')}
    # Docs updated.
    docs_modified(has_doc_files)
    # Misc/NEWS changed.
    reported_news(misc_files)
    # Regenerated configure, if necessary.
    regenerated_configure(file_paths)
    # Regenerated pyconfig.h.in, if necessary.
    regenerated_pyconfig_h_in(file_paths)

    # Test suite run and passed.
    has_c_files = any(fn for fn in file_paths if fn.endswith(('.c', '.h')))
    has_python_files = any(fn for fn in file_paths if fn.endswith('.py'))
    print()
    if has_c_files:
        print("Did you run the test suite and check for refleaks?")
    elif has_python_files:
        print("Did you run the test suite?")