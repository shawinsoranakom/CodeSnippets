def source_list(self) -> list[str] | None:
        """List of available input sources."""
        if self.available is False or (self.is_grouped and not self.is_leader):
            return None

        sources = [x.name for x in self._presets]

        # ignore if both id and text are None
        for input_ in self._inputs:
            if input_.text is not None:
                sources.append(input_.text)
            elif input_.id is not None:
                sources.append(input_.id)

        return sources