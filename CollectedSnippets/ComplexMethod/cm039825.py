def _get_class_level_metadata_request_values(cls, method: str):
        """Get class level metadata request values.

        This method first checks the `method`'s signature for passable metadata and then
        updates these with the metadata request values set at class level via the
        ``__metadata_request__{method}`` class attributes.

        This method (being a class-method), does not take request values set at
        instance level into account.
        """
        # Here we use `isfunction` instead of `ismethod` because calling `getattr`
        # on a class instead of an instance returns an unbound function.
        if not hasattr(cls, method) or not inspect.isfunction(getattr(cls, method)):
            return dict()
        # ignore the first parameter of the method, which is usually "self"
        signature_items = list(
            inspect.signature(getattr(cls, method)).parameters.items()
        )[1:]
        params = defaultdict(
            str,
            {
                param_name: None
                for param_name, param_info in signature_items
                if param_name not in {"X", "y", "Y", "Xt", "yt"}
                and param_info.kind
                not in {param_info.VAR_POSITIONAL, param_info.VAR_KEYWORD}
            },
        )
        # Then overwrite those defaults with the ones provided in
        # `__metadata_request__{method}` class attributes, which take precedence over
        # signature sniffing.

        # need to go through the MRO since this is a classmethod and
        # ``vars`` doesn't report the parent class attributes. We go through
        # the reverse of the MRO so that child classes have precedence over
        # their parents.
        substr = f"__metadata_request__{method}"
        for base_class in reversed(inspect.getmro(cls)):
            # Copy is needed with free-threaded context to avoid
            # RuntimeError: dictionary changed size during iteration.
            # copy.deepcopy applied on an instance of base_class adds
            # __slotnames__ attribute to base_class.
            base_class_items = vars(base_class).copy().items()
            for attr, value in base_class_items:
                # we don't check for equivalence since python prefixes attrs
                # starting with __ with the `_ClassName`.
                if substr not in attr:
                    continue
                for prop, alias in value.items():
                    # Here we add request values specified via those class attributes
                    # to the result dictionary (params). Adding a request which already
                    # exists will override the previous one. Since we go through the
                    # MRO in reverse order, the one specified by the lowest most classes
                    # in the inheritance tree are the ones which take effect.
                    if prop not in params and alias == UNUSED:
                        raise ValueError(
                            f"Trying to remove parameter {prop} with UNUSED which"
                            " doesn't exist."
                        )

                    params[prop] = alias

        return {param: alias for param, alias in params.items() if alias is not UNUSED}