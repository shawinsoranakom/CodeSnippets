def print_exc_group(typ, exc, tb, prefix=""):
        nonlocal group_depth
        group_depth += 1
        prefix2 = prefix or "  "
        if group_depth > max_group_depth:
            print(f"{prefix2}| ... (max_group_depth is {max_group_depth})",
                  file=efile)
            group_depth -= 1
            return
        if tb:
            if not prefix:
                print("  + Exception Group Traceback (most recent call last):", file=efile)
            else:
                print(f"{prefix}| Exception Group Traceback (most recent call last):", file=efile)
            tbe = traceback.extract_tb(tb)
            cleanup_traceback(tbe, exclude)
            for line in traceback.format_list(tbe):
                for subline in line.rstrip().splitlines():
                    print(f"{prefix2}| {subline}", file=efile)
        lines = get_message_lines(typ, exc, tb)
        for line in lines:
            print(f"{prefix2}| {line}", end="", file=efile)
        num_excs = len(exc.exceptions)
        if num_excs <= max_group_width:
            n = num_excs
        else:
            n = max_group_width + 1
        for i, sub in enumerate(exc.exceptions[:n], 1):
            truncated = (i > max_group_width)
            first_line_pre = "+-" if i == 1 else "  "
            title = str(i) if not truncated else '...'
            print(f"{prefix2}{first_line_pre}+---------------- {title} ----------------", file=efile)
            if truncated:
                remaining = num_excs - max_group_width
                plural = 's' if remaining > 1 else ''
                print(f"{prefix2}  | and {remaining} more exception{plural}",
                      file=efile)
                need_print_underline = True
            elif id(sub) not in seen:
                if not prefix:
                    print_exc(type(sub), sub, sub.__traceback__, "    ")
                else:
                    print_exc(type(sub), sub, sub.__traceback__, prefix + "  ")
                need_print_underline = not isinstance(sub, BaseExceptionGroup)
            else:
                print(f"{prefix2}  | <exception {type(sub).__name__} has printed>", file=efile)
                need_print_underline = True
            if need_print_underline and i == n:
                print(f"{prefix2}  +------------------------------------", file=efile)
        group_depth -= 1