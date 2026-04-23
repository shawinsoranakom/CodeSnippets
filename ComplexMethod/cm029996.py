def _batch_setitems(self, items, obj):
        # Helper to batch up SETITEMS sequences; proto >= 1 only
        save = self.save
        write = self.write

        if not self.bin:
            for k, v in items:
                save(k)
                try:
                    save(v)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} item {k!r}')
                    raise
                write(SETITEM)
            return

        for batch in batched(items, self._BATCHSIZE):
            if len(batch) != 1:
                write(MARK)
                for k, v in batch:
                    save(k)
                    try:
                        save(v)
                    except BaseException as exc:
                        exc.add_note(f'when serializing {_T(obj)} item {k!r}')
                        raise
                write(SETITEMS)
            else:
                k, v = batch[0]
                save(k)
                try:
                    save(v)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} item {k!r}')
                    raise
                write(SETITEM)