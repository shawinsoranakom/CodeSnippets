def __reversed__(self) -> Iterator[Self]:
        """ Return an reversed iterator over ``self``. """
        # same as __iter__ but reversed
        ids = self._ids
        size = len(ids)
        if size <= 1:
            if size == 1:
                yield self
            return
        cls = self.__class__
        env = self.env
        prefetch_ids = self._prefetch_ids
        if size > PREFETCH_MAX and prefetch_ids is ids:
            for sub_ids in split_every(PREFETCH_MAX, reversed(ids)):
                for id_ in sub_ids:
                    yield cls(env, (id_,), sub_ids)
        else:
            prefetch_ids = ReversedIterable(prefetch_ids)
            for id_ in reversed(ids):
                yield cls(env, (id_,), prefetch_ids)