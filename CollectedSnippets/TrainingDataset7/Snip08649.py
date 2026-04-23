def __init__(self, *args, file_path=None, **kwargs):
        self._fname = None
        if file_path is not None:
            self.file_path = file_path
        else:
            self.file_path = getattr(settings, "EMAIL_FILE_PATH", None)
        self.file_path = os.path.abspath(self.file_path)
        try:
            os.makedirs(self.file_path, exist_ok=True)
        except FileExistsError:
            raise ImproperlyConfigured(
                "Path for saving email messages exists, but is not a directory: %s"
                % self.file_path
            )
        except OSError as err:
            raise ImproperlyConfigured(
                "Could not create directory for saving email messages: %s (%s)"
                % (self.file_path, err)
            )
        # Make sure that self.file_path is writable.
        if not os.access(self.file_path, os.W_OK):
            raise ImproperlyConfigured(
                "Could not write to directory: %s" % self.file_path
            )
        # Finally, call super().
        # Since we're using the console-based backend as a base,
        # force the stream to be None, so we don't default to stdout
        kwargs["stream"] = None
        super().__init__(*args, **kwargs)