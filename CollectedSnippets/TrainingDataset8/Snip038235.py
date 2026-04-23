def __exit__(self, exc_type, exc_value, exc_traceback):
        shutil.rmtree(self._path)