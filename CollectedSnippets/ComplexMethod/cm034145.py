def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        try:
            init_class = cls._init_class  # type: ignore[attr-defined]
        except AttributeError:
            pass
        else:
            init_class()

        if not cls._subclasses_native_type:
            return  # NOTE: When not subclassing a native type, the derived type must set cls._native_type itself and cls._empty_tags_as_native to False.

        try:
            # Subclasses of tagged types will already have a native type set and won't need to detect it.
            # Special types which do not subclass a native type can also have their native type already set.
            # Automatic item source selection is only implemented for types that don't set _native_type.
            cls._native_type
        except AttributeError:
            # Direct subclasses of native types won't have cls._native_type set, so detect the native type.
            cls._native_type = cls.__bases__[0]

            # Detect the item source if not already set.
            if cls._item_source is None and is_non_scalar_collection_type(cls._native_type):
                cls._item_source = cls._native_type.__iter__  # type: ignore[attr-defined]

        # Use a collection specific factory for types with item sources.
        if cls._item_source:
            cls._instance_factory = cls._instance_factory_collection  # type: ignore[method-assign]

        new_type_direct_subclass = cls.__mro__[1]

        conflicting_impl = AnsibleTaggedObject._tagged_type_map.get(new_type_direct_subclass)

        if conflicting_impl:
            raise TypeError(f'Cannot define type {cls.__name__!r} since {conflicting_impl.__name__!r} already extends {new_type_direct_subclass.__name__!r}.')

        AnsibleTaggedObject._tagged_type_map[new_type_direct_subclass] = cls

        if is_non_scalar_collection_type(cls):
            AnsibleTaggedObject._tagged_collection_types.add(cls)
            AnsibleTaggedObject._collection_types.update({cls, new_type_direct_subclass})