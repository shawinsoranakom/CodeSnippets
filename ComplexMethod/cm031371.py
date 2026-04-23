def getpending(self) -> Event:
        """Return the characters that have been typed but not yet
        processed."""
        e = Event("key", "", b"")

        while not self.event_queue.empty():
            e2 = self.event_queue.get()
            if e2:
                e.data += e2.data

        recs, rec_count = self._read_input_bulk(1024)
        for i in range(rec_count):
            rec = recs[i]
            # In case of a legacy console, we do not only receive a keydown
            # event, but also a keyup event - and for uppercase letters
            # an additional SHIFT_PRESSED event.
            if rec and rec.EventType == KEY_EVENT:
                key_event = rec.Event.KeyEvent
                if not key_event.bKeyDown:
                    continue
                ch = key_event.uChar.UnicodeChar
                if ch == "\x00":
                    # ignore SHIFT_PRESSED and special keys
                    continue
                if ch == "\r":
                    ch = "\n"
                e.data += ch
        return e