def post_init(cls) -> None:
        cls.datatag_instances = [value for value, _repr in cls.tag_instances_with_reprs]
        cls.serializable_instances = [value for value in (
            cls.datatag_instances + cls.tagged_object_instances + message_instances) if cls.is_type_applicable(value)]
        cls.serializable_instances_with_instance_copy = [t.cast(CopyProtocol, item) for item in cls.serializable_instances if hasattr(item, 'copy')]
        # NOTE: this doesn't include the lazy template types, those are tested separately
        cls.serializable_types = [value for value in (
            list(AnsibleSerializable._known_type_map.values()) + [AnsibleSerializable]) if cls.is_type_applicable(value)]