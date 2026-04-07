def item_attributes(self, item):
        attrs = super().item_attributes(item)
        attrs["bacon"] = "yum"
        return attrs