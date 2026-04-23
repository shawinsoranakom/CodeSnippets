def end_object(self, obj):
        # self._current has the field data
        json.dump(self.get_dump_object(obj), self.stream, **self.json_kwargs)
        self.stream.write("\n")
        self._current = None