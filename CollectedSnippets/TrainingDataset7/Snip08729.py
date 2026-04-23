def get_check_kwargs(self, options):
        if self.requires_system_checks == ALL_CHECKS:
            return {}
        return {"tags": self.requires_system_checks}