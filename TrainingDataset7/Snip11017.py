def _check_deprecation_details(self):
        if self.system_check_removed_details is not None:
            return [
                checks.Error(
                    self.system_check_removed_details.get(
                        "msg",
                        "%s has been removed except for support in historical "
                        "migrations." % self.__class__.__name__,
                    ),
                    hint=self.system_check_removed_details.get("hint"),
                    obj=self,
                    id=self.system_check_removed_details.get("id", "fields.EXXX"),
                )
            ]
        elif self.system_check_deprecated_details is not None:
            return [
                checks.Warning(
                    self.system_check_deprecated_details.get(
                        "msg", "%s has been deprecated." % self.__class__.__name__
                    ),
                    hint=self.system_check_deprecated_details.get("hint"),
                    obj=self,
                    id=self.system_check_deprecated_details.get("id", "fields.WXXX"),
                )
            ]
        return []