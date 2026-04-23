def get_exception_traceback_frames(self, exc_value, tb):
        exc_cause = self._get_explicit_or_implicit_cause(exc_value)
        exc_cause_explicit = getattr(exc_value, "__cause__", True)
        if tb is None:
            yield {
                "exc_cause": exc_cause,
                "exc_cause_explicit": exc_cause_explicit,
                "tb": None,
                "type": "user",
            }
        while tb is not None:
            # Support for __traceback_hide__ which is used by a few libraries
            # to hide internal frames.
            if tb.tb_frame.f_locals.get("__traceback_hide__"):
                tb = tb.tb_next
                continue
            filename = tb.tb_frame.f_code.co_filename
            function = tb.tb_frame.f_code.co_name
            lineno = tb.tb_lineno - 1
            loader = tb.tb_frame.f_globals.get("__loader__")
            module_name = tb.tb_frame.f_globals.get("__name__") or ""
            (
                pre_context_lineno,
                pre_context,
                context_line,
                post_context,
            ) = self._get_lines_from_file(
                filename,
                lineno,
                7,
                loader,
                module_name,
            )
            if pre_context_lineno is None:
                pre_context_lineno = lineno
                pre_context = []
                context_line = "<source code not available>"
                post_context = []

            colno = tb_area_colno = ""
            _, _, start_column, end_column = next(
                itertools.islice(
                    tb.tb_frame.f_code.co_positions(), tb.tb_lasti // 2, None
                )
            )
            if start_column and end_column:
                underline = "^" * (end_column - start_column)
                spaces = " " * (start_column + len(str(lineno + 1)) + 2)
                colno = f"\n{spaces}{underline}"
                tb_area_spaces = " " * (
                    4 + start_column - (len(context_line) - len(context_line.lstrip()))
                )
                tb_area_colno = f"\n{tb_area_spaces}{underline}"
            yield {
                "exc_cause": exc_cause,
                "exc_cause_explicit": exc_cause_explicit,
                "tb": tb,
                "type": "django" if module_name.startswith("django.") else "user",
                "filename": filename,
                "function": function,
                "lineno": lineno + 1,
                "vars": self.filter.get_traceback_frame_variables(
                    self.request, tb.tb_frame
                ),
                "id": id(tb),
                "pre_context": pre_context,
                "context_line": context_line,
                "post_context": post_context,
                "pre_context_lineno": pre_context_lineno + 1,
                "colno": colno,
                "tb_area_colno": tb_area_colno,
            }
            tb = tb.tb_next