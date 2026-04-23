def source(self) -> str | None:
        """Name of the current input source."""
        if self.available is False or (self.is_grouped and not self.is_leader):
            return None

        if self._status.input_id is not None:
            for input_ in self._inputs:
                # the input might not have an id => also try to match on the stream_url/url
                # we have to use both because neither matches all the time
                if (
                    input_.id == self._status.input_id
                    or input_.url == self._status.stream_url
                ):
                    return input_.text if input_.text is not None else input_.id

        for preset in self._presets:
            if preset.url == self._status.stream_url:
                return preset.name

        return self._status.service