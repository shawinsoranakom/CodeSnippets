def root_attributes(self):
        attrs = super().root_attributes()
        attrs["django"] = "rocks"
        return attrs