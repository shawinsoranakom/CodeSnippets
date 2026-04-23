def _get_async_objs(self) -> AsyncObjects:
        """Return our AsyncObjects instance. If the Runtime hasn't been
        started, this will raise an error.
        """
        if self._async_objs is None:
            raise RuntimeError("Runtime hasn't started yet!")
        return self._async_objs