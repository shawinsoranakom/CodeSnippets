def item_extra_kwargs(self, item):
        return {"geometry": self._get_dynamic_attr("item_geometry", item)}