def __str__(self):
        params_str = "".join("; %s=%s" % (k, v) for k, v in self.params.items())
        return "%s%s%s" % (
            self.main_type,
            ("/%s" % self.sub_type) if self.sub_type else "",
            params_str,
        )