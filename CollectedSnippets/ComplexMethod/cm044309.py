def wrapper(*f_args, **f_kwargs):
        try:
            return func(*f_args, **f_kwargs)
        except (ValidationError, OpenBBError, Exception) as e:
            if Env().DEBUG_MODE:
                raise

            # Get the last traceback object from the exception
            tb = e.__traceback__
            if tb:
                while tb.tb_next is not None:
                    tb = tb.tb_next

            if isinstance(e, ValidationError):
                error_list: list = []
                validation_error = f"{e.error_count()} validations error(s)"
                for err in e.errors(include_url=False):
                    loc = ".".join(
                        [
                            str(i)
                            for i in err.get("loc", ())
                            if i
                            not in (
                                "standard_params",
                                "extra_params",
                                "provider_choices",
                            )
                        ]
                    )
                    msg = err.get("msg", "")
                    _input = (
                        "..."
                        if msg == "Missing required argument"
                        else err.get("input", "")
                    )
                    prefix = f"[Data Model] {e.title}\n" if "Data" in e.title else ""
                    error_list.append(
                        f"{prefix}[Arg] {loc} -> input: {_input} -> {msg}"
                    )
                error_list.insert(0, validation_error)
                error_str = "\n".join(error_list)
                raise OpenBBError(f"\n[Error] -> {error_str}").with_traceback(
                    tb
                ) from None
            if isinstance(e, UnauthorizedError):
                raise UnauthorizedError(f"\n[Error] -> {e}").with_traceback(
                    tb
                ) from None
            if isinstance(e, EmptyDataError):
                raise EmptyDataError(f"\n[Empty] -> {e}").with_traceback(tb) from None
            if isinstance(e, OpenBBError):
                raise OpenBBError(f"\n[Error] -> {e}").with_traceback(tb) from None
            if isinstance(e, Exception):
                raise OpenBBError(
                    f"\n[Unexpected Error] -> {e.__class__.__name__} -> {e}"
                ).with_traceback(tb) from None

        return None