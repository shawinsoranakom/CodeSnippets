def _handle_input(self) -> bool:
        """Handle keyboard input.

        Returns:
            True to continue, False to exit
        """
        ch = _getch()

        # Tab - next category
        if ch == "\t":
            self.current_tab = (self.current_tab + 1) % len(self.categories)
            self.selected_index = 0
            return True

        # Shift+Tab - previous category
        if ch == "shift_tab":
            self.current_tab = (self.current_tab - 1) % len(self.categories)
            self.selected_index = 0
            return True

        # Number keys 1-9 - jump to category
        if ch in "123456789":
            idx = int(ch) - 1
            if idx < len(self.categories):
                self.current_tab = idx
                self.selected_index = 0
            return True

        # Arrow up
        if ch == "\x1b[A":
            category = self.categories[self.current_tab]
            settings = category.get_settings(self.all_settings)
            if settings:
                self.selected_index = (self.selected_index - 1) % len(settings)
            return True

        # Arrow down
        if ch == "\x1b[B":
            category = self.categories[self.current_tab]
            settings = category.get_settings(self.all_settings)
            if settings:
                self.selected_index = (self.selected_index + 1) % len(settings)
            return True

        # Arrow left - previous category
        if ch == "\x1b[D":
            self.current_tab = (self.current_tab - 1) % len(self.categories)
            self.selected_index = 0
            return True

        # Arrow right - next category
        if ch == "\x1b[C":
            self.current_tab = (self.current_tab + 1) % len(self.categories)
            self.selected_index = 0
            return True

        # Enter - edit selected setting
        if ch in ("\r", "\n"):
            self._edit_current_setting()
            return True

        # S - save
        if ch in ("s", "S"):
            self._save_settings()
            return True

        # Q - quit
        if ch in ("q", "Q"):
            if self.has_unsaved_changes:
                return self._confirm_quit()
            return False

        # Ctrl+C
        if ch == "\x03":
            raise KeyboardInterrupt()

        return True