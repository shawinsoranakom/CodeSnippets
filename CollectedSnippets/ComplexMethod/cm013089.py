def _post_process_for_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """:func:`torch.export.export` requires dynamic shapes and keyword arguments
        that are not part of the explicit function signature but are collected via
        ``**<kwargs_name>`` to be wrapped under the corresponding parameter name
        (``self.kwargs_name``) as ``{<kwargs_name>: {'param': shape or tensor}}``.
        This function ensures this wrapping is performed when ``self.kwargs_name`` is set.
        """
        if not self.kwargs_name:
            # Nothing to do here.
            return kwargs
        to_be_moved = {k for k in kwargs if k not in self.signature_names}
        if not to_be_moved:
            return kwargs
        keywords = {k: v for k, v in kwargs.items() if k in to_be_moved}
        new_kwargs = {k: v for k, v in kwargs.items() if k not in to_be_moved}
        if self.kwargs_name in new_kwargs:
            raise ValueError(
                f"Keyword argument name collision: received a keyword argument "
                f"'{self.kwargs_name}' which conflicts with the **{self.kwargs_name} "
                "parameter used to collect extra keyword arguments. "
                "Passing a keyword argument with this name is not supported."
            )
        return {**new_kwargs, self.kwargs_name: keywords}