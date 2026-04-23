def _existing_object(self, pk):
        if not hasattr(self, "_object_dict"):
            self._object_dict = {o.pk: o for o in self.get_queryset()}
        return self._object_dict.get(pk)