def __copy__(self):
        obj = super().__copy__()
        # Remove any cached PathInfo values.
        obj.__dict__.pop("path_infos", None)
        obj.__dict__.pop("reverse_path_infos", None)
        return obj