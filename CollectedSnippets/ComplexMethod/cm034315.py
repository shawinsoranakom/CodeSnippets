def replace_stderr_clixml(stderr: bytes) -> bytes:
    """Replace CLIXML with stderr data.

    Tries to replace an embedded CLIXML string with the actual stderr data. If
    it fails to parse the CLIXML data, it will return the original data. This
    will replace any line inside the stderr string that contains a valid CLIXML
    sequence.

    :param bytes stderr: The stderr to try and decode.
    :returns: The stderr with the decoded CLIXML data or the original data.
    """
    clixml_header = b"#< CLIXML"

    # Instead of checking both patterns we just see if the next char
    # is \r or \n to match both Windows and POSIX newline after the marker.
    clixml_idx = stderr.find(clixml_header)
    if clixml_idx == -1:
        return stderr

    newline_idx = clixml_idx + 9
    if len(stderr) < (newline_idx + 1) or stderr[newline_idx] not in (ord(b'\r'), ord(b'\n')):
        return stderr

    lines: list[bytes] = []
    is_clixml = False
    for line in stderr.splitlines(True):
        if is_clixml:
            is_clixml = False

            # If the line does not contain the closing CLIXML tag, we just
            # add the found header line and this line without trying to parse.
            end_idx = line.find(b"</Objs>")
            if end_idx == -1:
                lines.append(clixml_header)
                lines.append(line)
                continue

            clixml = line[: end_idx + 7]
            remaining = line[end_idx + 7 :]

            # While we expect the stderr to be UTF-8 encoded, we fallback to
            # the most common "ANSI" codepage used by Windows cp437 if it is
            # not valid UTF-8.
            try:
                clixml_text = clixml.decode("utf-8")
            except UnicodeDecodeError:
                clixml_text = clixml.decode("cp437")

            try:
                decoded_clixml = extract_clixml_strings(clixml_text, stream="Error")
                lines.append("".join(decoded_clixml).encode('utf-8', errors='surrogatepass'))
                if remaining:
                    lines.append(remaining)

            except Exception:
                # Any errors and we just add the original CLIXML header and
                # line back in.
                lines.append(clixml_header)
                lines.append(line)

        elif line.startswith(clixml_header):
            # The next line should contain the full CLIXML data.
            clixml_header = line  # Preserve original newlines value.
            is_clixml = True

        else:
            lines.append(line)

    # This should never happen but if there was a CLIXML header without a newline
    # following it, we need to add it back.
    if is_clixml:
        lines.append(clixml_header)

    # PowerShell 7 is not consistent at all with disabling VT color codes,
    # especially in the CLIXML stderr. Instead of trying to hack it in through
    # env vars that may or may not work we just strip it from the output.
    return _VT_COLOR_PATTERN.sub(b"", b"".join(lines))