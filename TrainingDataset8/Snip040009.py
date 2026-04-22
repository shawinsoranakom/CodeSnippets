def create_metadata(id, value_type):
    return WidgetMetadata(id, lambda x, s: x, identity, value_type)