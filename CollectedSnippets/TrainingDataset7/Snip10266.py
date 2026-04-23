def describe(self):
        return "Create %smodel %s" % (
            "proxy " if self.options.get("proxy", False) else "",
            self.name,
        )