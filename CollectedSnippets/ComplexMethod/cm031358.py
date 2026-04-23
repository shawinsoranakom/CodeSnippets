def handle1(self, block: bool = True) -> bool:
        """Handle a single event.  Wait as long as it takes if block
        is true (the default), otherwise return False if no event is
        pending."""

        if self.msg:
            self.msg = ""
            self.invalidate_message()

        while True:
            # We use the same timeout as in readline.c: 100ms
            self.run_hooks()
            self.console.wait(100)
            event = self.console.get_event(block=False)
            if not event:
                if block:
                    continue
                return False

            translate = True

            if event.evt == "key":
                self.input_trans.push(event)
            elif event.evt == "scroll":
                self.invalidate_full()
                self.refresh()
                return True
            elif event.evt == "resize":
                self.invalidate_full()
                self.refresh()
                return True
            else:
                translate = False

            if translate:
                cmd = self.input_trans.get()
            else:
                cmd = [event.evt, event.data]

            if cmd is None:
                if block:
                    continue
                return False

            self.do_cmd(cmd)
            return True