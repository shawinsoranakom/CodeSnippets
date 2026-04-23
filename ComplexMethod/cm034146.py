def __init_subclass__(cls, **kwargs) -> None:
        cls.deserialize_map = {}
        cls._common_discard_tags = {obj: cls.discard_tags for obj in _common_module_types if issubclass(obj, AnsibleTaggedObject)}

        cls.post_init()

        cls.profile_name = cls.__module__.rsplit('.', maxsplit=1)[-1].lstrip('_')

        wrapper_types = set(obj for obj in cls.serialize_map.values() if isinstance(obj, type) and issubclass(obj, AnsibleSerializableWrapper))

        cls.allowed_ansible_serializable_types |= wrapper_types

        # no current need to preserve tags on controller-only types or custom behavior for anything in `allowed_serializable_types`
        cls.serialize_map.update({obj: cls.serialize_serializable_object for obj in cls.allowed_ansible_serializable_types})
        cls.serialize_map.update({obj: func for obj, func in _internal.get_controller_serialize_map().items() if obj not in cls.serialize_map})

        cls.deserialize_map[AnsibleSerializable._TYPE_KEY] = cls.deserialize_serializable  # always recognize tagged types

        cls._allowed_type_keys = frozenset(obj._type_key for obj in cls.allowed_ansible_serializable_types)

        cls._unwrapped_json_types = frozenset(
            {obj for obj in cls.serialize_map if not issubclass(obj, _json_types)}  # custom types that do not extend JSON-native types
            | {obj for obj in _json_scalar_types if obj not in cls.serialize_map}  # JSON-native scalars lacking custom handling
        )