def __init__(self, *args, manifest_storage=None, **kwargs):
        manifest_storage = storage.StaticFilesStorage(
            location=kwargs.pop("manifest_location"),
        )
        super().__init__(*args, manifest_storage=manifest_storage, **kwargs)