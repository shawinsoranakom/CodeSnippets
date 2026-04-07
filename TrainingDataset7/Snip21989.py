def __iter__(self):
                for item in super().__iter__():
                    item_type, meta_data, field_stream = item
                    yield item_type, meta_data, field_stream
                    if item_type == FILE:
                        return