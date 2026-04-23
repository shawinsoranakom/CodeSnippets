def __init__(self, *args, **kwargs):
        if not hasattr(self, "_get_single_internal"):
            self._get_single_internal = self._get_single_external

        if not hasattr(self, "_set_single"):
            self._set_single = self._set_single_rebuild
            self._assign_extended_slice = self._assign_extended_slice_rebuild

        super().__init__(*args, **kwargs)