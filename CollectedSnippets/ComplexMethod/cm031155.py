def _write_data(writer, text, attr):
    "Writes datachars to writer."
    if not text:
        return
    # See the comments in ElementTree.py for behavior and
    # implementation details.
    if "&" in text:
        text = text.replace("&", "&amp;")
    if "<" in text:
        text = text.replace("<", "&lt;")
    if ">" in text:
        text = text.replace(">", "&gt;")
    if attr:
        if '"' in text:
            text = text.replace('"', "&quot;")
        if "\r" in text:
            text = text.replace("\r", "&#13;")
        if "\n" in text:
            text = text.replace("\n", "&#10;")
        if "\t" in text:
            text = text.replace("\t", "&#9;")
    writer.write(text)