def end_object(self, obj):
        self.objects.append(self.get_dump_object(obj))
        self._current = None