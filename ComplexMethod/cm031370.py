def get_event(self, block: bool = True) -> Event | None:
        """Return an Event instance.  Returns None if |block| is false
        and there is no event pending, otherwise waits for the
        completion of an event."""

        if not block and not self.wait(timeout=0):
            return None

        while self.event_queue.empty():
            rec = self._read_input()
            if rec is None:
                return None

            if rec.EventType == WINDOW_BUFFER_SIZE_EVENT:
                return Event("resize", "")

            if rec.EventType != KEY_EVENT or not rec.Event.KeyEvent.bKeyDown:
                # Only process keys and keydown events
                if block:
                    continue
                return None

            key_event = rec.Event.KeyEvent
            raw_key = key = key_event.uChar.UnicodeChar

            if key == "\r":
                # Make enter unix-like
                return Event(evt="key", data="\n")
            elif key_event.wVirtualKeyCode == 8:
                # Turn backspace directly into the command
                key = "backspace"
            elif key == "\x00":
                # Handle special keys like arrow keys and translate them into the appropriate command
                key = VK_MAP.get(key_event.wVirtualKeyCode)
                if key:
                    if key_event.dwControlKeyState & CTRL_ACTIVE:
                        key = f"ctrl {key}"
                    elif key_event.dwControlKeyState & ALT_ACTIVE:
                        # queue the key, return the meta command
                        self.event_queue.insert(Event(evt="key", data=key))
                        return Event(evt="key", data="\033")  # keymap.py uses this for meta
                    return Event(evt="key", data=key)
                if block:
                    continue

                return None
            elif self.__vt_support:
                # If virtual terminal is enabled, scanning VT sequences
                for char in raw_key.encode(self.event_queue.encoding, "replace"):
                    self.event_queue.push(char)
                continue

            if key_event.dwControlKeyState & ALT_ACTIVE:
                # Do not swallow characters that have been entered via AltGr:
                # Windows internally converts AltGr to CTRL+ALT, see
                # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscanw
                if not key_event.dwControlKeyState & CTRL_ACTIVE:
                    # queue the key, return the meta command
                    self.event_queue.insert(Event(evt="key", data=key))
                    return Event(evt="key", data="\033")  # keymap.py uses this for meta

            return Event(evt="key", data=key)
        return self.event_queue.get()