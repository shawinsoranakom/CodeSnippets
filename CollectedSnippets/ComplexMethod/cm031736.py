def linear_format(text: str, **kwargs: str) -> str:
    """
    Perform str.format-like substitution, except:
      * The strings substituted must be on lines by
        themselves.  (This line is the "source line".)
      * If the substitution text is empty, the source line
        is removed in the output.
      * If the field is not recognized, the original line
        is passed unmodified through to the output.
      * If the substitution text is not empty:
          * Each line of the substituted text is indented
            by the indent of the source line.
          * A newline will be added to the end.
    """
    lines = []
    for line in text.split("\n"):
        indent, curly, trailing = line.partition("{")
        if not curly:
            lines.extend([line, "\n"])
            continue

        name, curly, trailing = trailing.partition("}")
        if not curly or name not in kwargs:
            lines.extend([line, "\n"])
            continue

        if trailing:
            raise ClinicError(
                f"Text found after '{{{name}}}' block marker! "
                "It must be on a line by itself."
            )
        if indent.strip():
            raise ClinicError(
                f"Non-whitespace characters found before '{{{name}}}' block marker! "
                "It must be on a line by itself."
            )

        value = kwargs[name]
        if not value:
            continue

        stripped = [line.rstrip() for line in value.split("\n")]
        value = textwrap.indent("\n".join(stripped), indent)
        lines.extend([value, "\n"])

    return "".join(lines[:-1])