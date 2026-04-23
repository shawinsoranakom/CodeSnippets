def get_browser_logs(self, source=None, level="ALL"):
        """
        Return Chrome console logs filtered by level and optionally source.
        """
        try:
            logs = self.selenium.get_log("browser")
        except AttributeError:
            logs = []
        return [
            log
            for log in logs
            if (level == "ALL" or log["level"] == level)
            and (source is None or log["source"] == source)
        ]