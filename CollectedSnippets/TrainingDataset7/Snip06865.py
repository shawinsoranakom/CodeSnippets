def feed_extra_kwargs(self, obj):
        return {"geometry": self._get_dynamic_attr("geometry", obj)}