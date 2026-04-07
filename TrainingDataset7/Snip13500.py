def __getstate__(self):
        """
        Raise an exception if trying to pickle an unrendered response. Pickle
        only rendered data, not the data used to construct the response.
        """
        obj_dict = self.__dict__.copy()
        if not self._is_rendered:
            raise ContentNotRenderedError(
                "The response content must be rendered before it can be pickled."
            )
        for attr in self.rendering_attrs:
            if attr in obj_dict:
                del obj_dict[attr]

        return obj_dict