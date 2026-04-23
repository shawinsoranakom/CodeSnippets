def as_keyed_widget_id(raw_wid, key):
    return f"{GENERATED_WIDGET_KEY_PREFIX}-{raw_wid}-{key}"