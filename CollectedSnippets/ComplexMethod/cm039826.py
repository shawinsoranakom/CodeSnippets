def func(*args, **kw):
            """Updates the `_metadata_request` attribute of the consumer (`instance`)
            for the parameters provided as `**kw`.

            This docstring is overwritten below.
            See REQUESTER_DOC for expected functionality.
            """
            if not _routing_enabled():
                raise RuntimeError(
                    "This method is only available when metadata routing is enabled."
                    " You can enable it using"
                    " sklearn.set_config(enable_metadata_routing=True)."
                )

            if self.validate_keys and (set(kw) - set(self.keys)):
                raise TypeError(
                    f"Unexpected args: {set(kw) - set(self.keys)} in {self.name}. "
                    f"Accepted arguments are: {set(self.keys)}"
                )

            # This makes it possible to use the decorated method as an unbound method,
            # for instance when monkeypatching.
            # https://github.com/scikit-learn/scikit-learn/issues/28632
            if instance is None:
                _instance = args[0]
                args = args[1:]
            else:
                _instance = instance

            # Replicating python's behavior when positional args are given other than
            # `self`, and `self` is only allowed if this method is unbound.
            if args:
                raise TypeError(
                    f"set_{self.name}_request() takes 0 positional argument but"
                    f" {len(args)} were given"
                )

            requests = _instance._get_metadata_request()
            method_metadata_request = getattr(requests, self.name)

            for prop, alias in kw.items():
                if alias is not UNCHANGED:
                    method_metadata_request.add_request(param=prop, alias=alias)
            _instance._metadata_request = requests

            return _instance