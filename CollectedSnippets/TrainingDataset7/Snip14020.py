def enable(self):
        self.old_prefix = get_script_prefix()
        set_script_prefix(self.prefix)