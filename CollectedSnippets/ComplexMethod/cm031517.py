def print_exc(typ, exc, tb, prefix=""):
        seen.add(id(exc))
        context = exc.__context__
        cause = exc.__cause__
        prefix2 = f"{prefix}| " if prefix else ""
        if cause is not None and id(cause) not in seen:
            print_exc(type(cause), cause, cause.__traceback__, prefix)
            print(f"{prefix2}\n{prefix2}The above exception was the direct cause "
                  f"of the following exception:\n{prefix2}", file=efile)
        elif (context is not None and
              not exc.__suppress_context__ and
              id(context) not in seen):
            print_exc(type(context), context, context.__traceback__, prefix)
            print(f"{prefix2}\n{prefix2}During handling of the above exception, "
                  f"another exception occurred:\n{prefix2}", file=efile)
        if isinstance(exc, BaseExceptionGroup):
            print_exc_group(typ, exc, tb, prefix=prefix)
        else:
            if tb:
                print(f"{prefix2}Traceback (most recent call last):", file=efile)
                tbe = traceback.extract_tb(tb)
                cleanup_traceback(tbe, exclude)
                if prefix:
                    for line in traceback.format_list(tbe):
                        for subline in line.rstrip().splitlines():
                            print(f"{prefix}| {subline}", file=efile)
                else:
                    traceback.print_list(tbe, file=efile)
            lines = get_message_lines(typ, exc, tb)
            for line in lines:
                print(f"{prefix2}{line}", end="", file=efile)