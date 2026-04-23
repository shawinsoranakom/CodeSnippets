def __init__(self, *args, **kwargs):
            self._async_instance = async_class(*args, **kwargs)

            # Handle annotated class attributes (like execution: Execution)
            # Get all annotations from the class hierarchy and resolve string annotations
            try:
                # get_type_hints resolves string annotations to actual type objects
                # This handles classes using 'from __future__ import annotations'
                all_annotations = get_type_hints(async_class)
            except Exception:
                # Fallback to raw annotations if get_type_hints fails
                # (e.g., for undefined forward references)
                all_annotations = {}
                for base_class in reversed(inspect.getmro(async_class)):
                    if hasattr(base_class, "__annotations__"):
                        all_annotations.update(base_class.__annotations__)

            # For each annotated attribute, check if it needs to be created or wrapped
            for attr_name, attr_type in all_annotations.items():
                if hasattr(self._async_instance, attr_name):
                    # Attribute exists on the instance
                    attr = getattr(self._async_instance, attr_name)
                    # Check if this attribute needs a sync wrapper
                    if hasattr(attr, "__class__"):
                        from comfy_api.internal.singleton import ProxiedSingleton

                        if isinstance(attr, ProxiedSingleton):
                            # Create a sync version of this attribute
                            try:
                                sync_attr_class = cls.create_sync_class(attr.__class__)
                                # Create instance of the sync wrapper with the async instance
                                sync_attr = object.__new__(sync_attr_class)  # type: ignore
                                sync_attr._async_instance = attr
                                setattr(self, attr_name, sync_attr)
                            except Exception:
                                # If we can't create a sync version, keep the original
                                setattr(self, attr_name, attr)
                        else:
                            # Not async, just copy the reference
                            setattr(self, attr_name, attr)
                else:
                    # Attribute doesn't exist, but is annotated - create it
                    # This handles cases like execution: Execution
                    if isinstance(attr_type, type):
                        # Check if the type is defined as an inner class
                        if hasattr(async_class, attr_type.__name__):
                            inner_class = getattr(async_class, attr_type.__name__)
                            from comfy_api.internal.singleton import ProxiedSingleton

                            # Create an instance of the inner class
                            try:
                                # For ProxiedSingleton classes, get or create the singleton instance
                                if issubclass(inner_class, ProxiedSingleton):
                                    async_instance = inner_class.get_instance()
                                else:
                                    async_instance = inner_class()

                                # Create sync wrapper
                                sync_attr_class = cls.create_sync_class(inner_class)
                                sync_attr = object.__new__(sync_attr_class)  # type: ignore
                                sync_attr._async_instance = async_instance
                                setattr(self, attr_name, sync_attr)
                                # Also set on the async instance for consistency
                                setattr(self._async_instance, attr_name, async_instance)
                            except Exception as e:
                                logging.warning(
                                    f"Failed to create instance for {attr_name}: {e}"
                                )

            # Handle other instance attributes that might not be annotated
            for name, attr in inspect.getmembers(self._async_instance):
                if name.startswith("_") or hasattr(self, name):
                    continue

                # If attribute is an instance of a class, and that class is defined in the original class
                # we need to check if it needs a sync wrapper
                if isinstance(attr, object) and not isinstance(
                    attr, (str, int, float, bool, list, dict, tuple)
                ):
                    from comfy_api.internal.singleton import ProxiedSingleton

                    if isinstance(attr, ProxiedSingleton):
                        # Create a sync version of this nested class
                        try:
                            sync_attr_class = cls.create_sync_class(attr.__class__)
                            # Create instance of the sync wrapper with the async instance
                            sync_attr = object.__new__(sync_attr_class)  # type: ignore
                            sync_attr._async_instance = attr
                            setattr(self, name, sync_attr)
                        except Exception:
                            # If we can't create a sync version, keep the original
                            setattr(self, name, attr)