def test_serializable_instances_cover_all_concrete_impls(self):
        tested_types = {type(instance_type) for instance_type in self.serializable_instances}

        excluded_type_names = {
            AnsibleTaggedObject.__name__,  # base class, cannot be abstract
            AnsibleSerializableDataclass.__name__,  # base class, cannot be abstract
            AnsibleSerializable.__name__,  # base class, cannot be abstract
            AnsibleSerializableEnum.__name__,  # base class, cannot be abstract
            # these types are all controller-only, so it's easier to have static type names instead of importing them
            'JinjaConstTemplate',  # serialization not required
            '_EncryptedSource',  # serialization not required
            'CapturedErrorSummary',  # serialization not required
        }

        # don't require instances for types marked abstract or types that are clearly intended to be so (but can't be marked as such)
        required_types = {instance_type for instance_type in self.serializable_types if (
            not inspect.isabstract(instance_type) and
            not instance_type.__name__.endswith('Base') and
            'Lazy' not in instance_type.__name__ and  # lazy types use the same input data
            instance_type.__name__ not in excluded_type_names and
            not issubclass(instance_type, AnsibleSerializableWrapper)
        )}

        missing_types = required_types.difference(tested_types)

        assert not missing_types