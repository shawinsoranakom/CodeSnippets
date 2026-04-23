def load_backend(path):
    return import_string(path)()