def __init__(self, verbosity: int = 0) -> None:

        self._final_q: FinalQueue | None = None

        # NB: this lock is used to both prevent intermingled output between threads and to block writes during forks.
        # Do not change the type of this lock or upgrade to a shared lock (eg multiprocessing.RLock).
        self._lock = threading.RLock()

        self.columns = None
        self.verbosity = verbosity

        if C.LOG_VERBOSITY is None:
            self.log_verbosity = verbosity
        else:
            self.log_verbosity = max(verbosity, C.LOG_VERBOSITY)

        # list of all deprecation messages to prevent duplicate display
        self._deprecations: set[str] = set()
        self._warns: set[str] = set()
        self._errors: set[str] = set()

        self.b_cowsay: bytes | None = None
        self.noncow = C.ANSIBLE_COW_SELECTION

        self.set_cowsay_info()

        if self.b_cowsay:
            try:
                cmd = subprocess.Popen([self.b_cowsay, "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (out, err) = cmd.communicate()
                if cmd.returncode:
                    raise Exception
                self.cows_available: set[str] = {to_text(c) for c in out.split()}
                if C.ANSIBLE_COW_ACCEPTLIST and any(C.ANSIBLE_COW_ACCEPTLIST):
                    self.cows_available = set(C.ANSIBLE_COW_ACCEPTLIST).intersection(self.cows_available)
            except Exception:
                # could not execute cowsay for some reason
                self.b_cowsay = None

        self._set_column_width()

        try:
            # NB: we're relying on the display singleton behavior to ensure this only runs once
            _synchronize_textiowrapper(sys.stdout, self._lock)
            _synchronize_textiowrapper(sys.stderr, self._lock)
        except Exception as ex:
            self.warning(f"failed to patch stdout/stderr for fork-safety: {ex}")

        codecs.register_error('_replacing_warning_handler', self._replacing_warning_handler)
        try:
            sys.stdout.reconfigure(errors='_replacing_warning_handler')  # type: ignore[union-attr]
            sys.stderr.reconfigure(errors='_replacing_warning_handler')  # type: ignore[union-attr]
        except Exception as ex:
            self.warning(f"failed to reconfigure stdout/stderr with custom encoding error handler: {ex}")

        self.setup_curses = False