def open(self, url, new=0, autoraise=True):
        sys.audit("webbrowser.open", url)
        if new == 0:
            action = self.remote_action
        elif new == 1:
            action = self.remote_action_newwin
        elif new == 2:
            if self.remote_action_newtab is None:
                action = self.remote_action_newwin
            else:
                action = self.remote_action_newtab
        else:
            raise Error("Bad 'new' parameter to open(); "
                        f"expected 0, 1, or 2, got {new}")

        self._check_url(url.replace("%action", action))

        args = [arg.replace("%action", action).replace("%s", url)
                for arg in self.remote_args]
        args = [arg for arg in args if arg]
        success = self._invoke(args, True, autoraise, url)
        if not success:
            # remote invocation failed, try straight way
            args = [arg.replace("%s", url) for arg in self.args]
            return self._invoke(args, False, False)
        else:
            return True