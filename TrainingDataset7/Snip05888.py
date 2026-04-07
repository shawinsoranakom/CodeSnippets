def wait_for_and_switch_to_popup(self, num_windows=2, timeout=10):
        """
        Block until `num_windows` are present and are ready (usually 2, but can
        be overridden in the case of pop-ups opening other pop-ups). Switch the
        current window to the new pop-up.
        """
        self.wait_until(lambda d: len(d.window_handles) == num_windows, timeout)
        self.selenium.switch_to.window(self.selenium.window_handles[-1])
        self.wait_page_ready()