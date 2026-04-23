def _c(f):
        if f in EXCLUDE_FROM_LIB:
            return False
        if f.is_dir():
            if f in TEST_DIRS_ONLY:
                return ns.include_tests
            if f in TCLTK_DIRS_ONLY:
                return ns.include_tcltk
            if f in IDLE_DIRS_ONLY:
                return ns.include_idle
            if f in VENV_DIRS_ONLY:
                return ns.include_venv
        else:
            if f in TCLTK_FILES_ONLY:
                return ns.include_tcltk
        return True