def __init__(self, key_transform, *args, **kwargs):
        if not isinstance(key_transform, KeyTransform):
            raise TypeError(
                "Transform should be an instance of KeyTransform in order to "
                "use this lookup."
            )
        key_text_transform = KeyTextTransform(
            key_transform.key_name,
            *key_transform.source_expressions,
            **key_transform.extra,
        )
        super().__init__(key_text_transform, *args, **kwargs)