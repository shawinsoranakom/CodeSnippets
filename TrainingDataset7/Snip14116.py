def extract(path, to_path):
    """
    Unpack the tar or zip file at the specified path to the directory
    specified by to_path.
    """
    with Archive(path) as archive:
        archive.extract(to_path)