def __init__(self, path, /, *, flag, mode):
        if hasattr(self, "_cx"):
            raise error(_ERR_REINIT)

        path = os.fsdecode(path)
        match flag:
            case "r":
                flag = "ro"
            case "w":
                flag = "rw"
            case "c":
                flag = "rwc"
                Path(path).touch(mode=mode, exist_ok=True)
            case "n":
                flag = "rwc"
                Path(path).unlink(missing_ok=True)
                Path(path).touch(mode=mode)
            case _:
                raise ValueError("Flag must be one of 'r', 'w', 'c', or 'n', "
                                 f"not {flag!r}")

        # We use the URI format when opening the database.
        uri = _normalize_uri(path)
        uri = f"{uri}?mode={flag}"
        if flag == "ro":
            # Add immutable=1 to allow read-only SQLite access even if wal/shm missing
            uri += "&immutable=1"

        try:
            self._cx = sqlite3.connect(uri, autocommit=True, uri=True)
        except sqlite3.Error as exc:
            raise error(str(exc))

        if flag != "ro":
            # This is an optimization only; it's ok if it fails.
            with suppress(sqlite3.OperationalError):
                self._cx.execute("PRAGMA journal_mode = wal")

            if flag == "rwc":
                self._execute(BUILD_TABLE)