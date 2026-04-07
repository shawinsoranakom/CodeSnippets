def clear_delayed_apps_cache(self):
        if self.is_delayed and "apps" in self.__dict__:
            del self.__dict__["apps"]