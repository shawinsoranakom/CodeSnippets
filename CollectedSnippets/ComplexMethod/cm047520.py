def __repr__(self) -> str:
        # for debugging: show the cache content and dirty flags as stars
        data: dict[Field, dict] = {}
        for field, field_cache in sorted(self.transaction.field_data.items(), key=lambda item: str(item[0])):
            dirty_ids = self.transaction.field_dirty.get(field, ())
            if field in self.transaction.registry.field_depends_context:
                data[field] = {
                    key: {
                        Starred(id_) if id_ in dirty_ids else id_: val if field.type != 'binary' else '<binary>'
                        for id_, val in key_cache.items()
                    }
                    for key, key_cache in field_cache.items()
                }
            else:
                data[field] = {
                    Starred(id_) if id_ in dirty_ids else id_: val if field.type != 'binary' else '<binary>'
                    for id_, val in field_cache.items()
                }
        return repr(data)