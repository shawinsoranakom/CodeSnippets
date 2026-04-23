def showwarning_with_traceback(message, category, filename, lineno, file=None, line=None):
    if category is BytesWarning and message.args[0] in IGNORE:
        return

    # find the stack frame matching (filename, lineno)
    filtered = []
    for frame in traceback.extract_stack():
        if frame.name == '__call__' and frame.filename.endswith('/odoo/http.py'):
            # we don't care about the frames above our wsgi entrypoint
            filtered.clear()
        if 'importlib' not in frame.filename:
            filtered.append(frame)
        if frame.filename == filename and frame.lineno == lineno:
            break
    return showwarning(
        message, category, filename, lineno,
        file=file,
        line=''.join(traceback.format_list(filtered))
    )