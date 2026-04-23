def _get_awaited_by_tasks(pid: int, retries: int = 3) -> list:
    for attempt in range(retries + 1):
        try:
            return get_all_awaited_by(pid)
        except PermissionError:
            exit_with_permission_help_text()
        except ProcessLookupError:
            print(f"Error: process {pid} not found.", file=sys.stderr)
            sys.exit(1)
        except _TRANSIENT_ERRORS as e:
            if attempt < retries:
                continue
            if isinstance(e, RuntimeError):
                while e.__context__ is not None:
                    e = e.__context__
            print(f"Error retrieving tasks: {e}", file=sys.stderr)
            sys.exit(1)