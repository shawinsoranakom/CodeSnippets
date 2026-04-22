def _get_message_from_code(self, orig_exc: BaseException, cached_code, lineno: int):
        args = _get_error_message_args(orig_exc, cached_code)

        failing_lines = _get_failing_lines(cached_code, lineno)
        failing_lines_str = "".join(failing_lines)
        failing_lines_str = textwrap.dedent(failing_lines_str).strip("\n")

        args["failing_lines_str"] = failing_lines_str
        args["filename"] = cached_code.co_filename
        args["lineno"] = lineno

        # This needs to have zero indentation otherwise %(lines_str)s will
        # render incorrectly in Markdown.
        return (
            """
%(orig_exception_desc)s

Streamlit encountered an error while caching %(object_part)s %(object_desc)s.
This is likely due to a bug in `%(filename)s` near line `%(lineno)s`:

```
%(failing_lines_str)s
```

Please modify the code above to address this.

If you think this is actually a Streamlit bug, you may [file a bug report
here.] (https://github.com/streamlit/streamlit/issues/new/choose)
        """
            % args
        ).strip("\n")