def _batch_appends(self, items, obj):
        # Helper to batch up APPENDS sequences
        save = self.save
        write = self.write

        if not self.bin:
            for i, x in enumerate(items):
                try:
                    save(x)
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} item {i}')
                    raise
                write(APPEND)
            return

        start = 0
        for batch in batched(items, self._BATCHSIZE):
            batch_len = len(batch)
            if batch_len != 1:
                write(MARK)
                for i, x in enumerate(batch, start):
                    try:
                        save(x)
                    except BaseException as exc:
                        exc.add_note(f'when serializing {_T(obj)} item {i}')
                        raise
                write(APPENDS)
            else:
                try:
                    save(batch[0])
                except BaseException as exc:
                    exc.add_note(f'when serializing {_T(obj)} item {start}')
                    raise
                write(APPEND)
            start += batch_len