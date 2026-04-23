def modify(self, fileobj, events, data=None):
        try:
            key = self._fd_to_key[self._fileobj_lookup(fileobj)]
        except KeyError:
            raise KeyError(f"{fileobj!r} is not registered") from None

        changed = False
        if events != key.events:
            selector_events = ((events & EVENT_READ and self._EVENT_READ)
                               | (events & EVENT_WRITE and self._EVENT_WRITE))
            try:
                self._selector.modify(key.fd, selector_events)
            except:
                super().unregister(fileobj)
                raise
            changed = True
        if data != key.data:
            changed = True

        if changed:
            key = key._replace(events=events, data=data)
            self._fd_to_key[key.fd] = key
        return key