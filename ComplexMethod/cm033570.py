def visit(self, obj: t.Any) -> None:
        obj_id = id(obj)

        if obj_id in self.seen:
            return

        self.seen.add(obj_id)

        if TrustedAsTemplate.is_tagged_on(obj):
            raise TrustFoundError(obj)

        if isinstance(obj, (str, int, bool, types.NoneType)):
            pass  # expected scalar type
        elif isinstance(obj, (InventoryData, Host, Group)):
            self.visit(obj.__dict__)
        elif isinstance(obj, c.Mapping):
            for key, value in obj.items():
                self.visit(key)
                self.visit(value)
        elif isinstance(obj, c.Iterable):
            for item in obj:
                self.visit(item)
        else:
            raise TypeError(f'Checking of {type(obj)} is not supported.')