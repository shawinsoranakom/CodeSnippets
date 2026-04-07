def __getstate__(self):
        state = self.__dict__.copy()
        # Delete the path_infos cached property because it can be recalculated
        # at first invocation after deserialization. The attribute must be
        # removed because subclasses like ManyToOneRel may have a PathInfo
        # which contains an intermediate M2M table that's been dynamically
        # created and doesn't exist in the .models module.
        # This is a reverse relation, so there is no reverse_path_infos to
        # delete.
        state.pop("path_infos", None)
        return state