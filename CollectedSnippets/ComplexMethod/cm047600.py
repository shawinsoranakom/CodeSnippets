def __iter__(self) -> Iterator[Self]:
        """ Return an iterator over ``self``. """
        ids = self._ids
        size = len(ids)
        if size <= 1:
            # detect and handle small recordsets (single `1f`)
            # early return if no records and avoid allocation if we have a one
            if size == 1:
                yield self
            return
        cls = self.__class__
        env = self.env
        prefetch_ids = self._prefetch_ids
        if size > PREFETCH_MAX and prefetch_ids is ids:
            for sub_ids in split_every(PREFETCH_MAX, ids):
                for id_ in sub_ids:
                    yield cls(env, (id_,), sub_ids)
        else:
            for id_ in ids:
                yield cls(env, (id_,), prefetch_ids)