def write(self, text, interval=None, delay=0.30, **kwargs):
        """
        Type out a string of characters with some realistic delay.
        """
        time.sleep(delay / 2)

        if interval:
            pyautogui.write(text, interval=interval)
        else:
            try:
                clipboard_history = self.computer.clipboard.view()
            except:
                pass

            ends_in_enter = False

            if text.endswith("\n"):
                ends_in_enter = True
                text = text[:-1]

            lines = text.split("\n")

            if len(lines) < 5:
                for i, line in enumerate(lines):
                    line = line + "\n" if i != len(lines) - 1 else line
                    self.computer.clipboard.copy(line)
                    self.computer.clipboard.paste()
            else:
                # just do it all at once
                self.computer.clipboard.copy(text)
                self.computer.clipboard.paste()

            if ends_in_enter:
                self.press("enter")

            try:
                self.computer.clipboard.copy(clipboard_history)
            except:
                pass

        time.sleep(delay / 2)