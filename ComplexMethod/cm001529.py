def add_callback(callbacks, fun, *, name=None, category='unknown', filename=None):
    if filename is None:
        stack = [x for x in inspect.stack() if x.filename != __file__]
        filename = stack[0].filename if stack else 'unknown file'

    extension = extensions.find_extension(filename)
    extension_name = extension.canonical_name if extension else 'base'

    callback_name = f"{extension_name}/{os.path.basename(filename)}/{category}"
    if name is not None:
        callback_name += f'/{name}'

    unique_callback_name = callback_name
    for index in range(1000):
        existing = any(x.name == unique_callback_name for x in callbacks)
        if not existing:
            break

        unique_callback_name = f'{callback_name}-{index+1}'

    callbacks.append(ScriptCallback(filename, fun, unique_callback_name))