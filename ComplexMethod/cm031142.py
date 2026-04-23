def relative_to(self, other, *, walk_up=False):
        """Return the relative path to another path identified by the passed
        arguments.  If the operation is not possible (because this is not
        related to the other path), raise ValueError.

        The *walk_up* parameter controls whether `..` may be used to resolve
        the path.
        """
        if not hasattr(other, 'with_segments'):
            other = self.with_segments(other)
        parts = []
        for path in chain([other], other.parents):
            if path == self or path in self.parents:
                break
            elif not walk_up:
                raise ValueError(f"{str(self)!r} is not in the subpath of {str(other)!r}")
            elif path.name == '..':
                raise ValueError(f"'..' segment in {str(other)!r} cannot be walked")
            else:
                parts.append('..')
        else:
            raise ValueError(f"{str(self)!r} and {str(other)!r} have different anchors")
        parts.extend(self._tail[len(path._tail):])
        return self._from_parsed_parts('', '', parts)