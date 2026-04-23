def _route_params(self, params, parent, caller):
        """Prepare the given metadata to be passed to the method.

        The output of this method can be used directly as the input to the
        corresponding method as **kwargs.

        Parameters
        ----------
        params : dict
            A dictionary of provided metadata.

        parent : object
            Parent class object, that routes the metadata.

        caller : str
            Method from the parent class object, where the metadata is routed from.

        Returns
        -------
        params : Bunch
            A :class:`~sklearn.utils.Bunch` of {metadata: value} which can be
            passed to the corresponding method.
        """
        self._check_warnings(params=params)
        unrequested = dict()
        args = {arg: value for arg, value in params.items() if value is not None}
        res = Bunch()
        for prop, alias in self._requests.items():
            if alias is False or alias == WARN:
                continue
            elif alias is True and prop in args:
                res[prop] = args[prop]
            elif alias is None and prop in args:
                unrequested[prop] = args[prop]
            elif alias in args:
                res[prop] = args[alias]
        if unrequested:
            if self.method in COMPOSITE_METHODS:
                callee_methods = COMPOSITE_METHODS[self.method]
            else:
                callee_methods = [self.method]
            set_requests_on = "".join(
                [
                    f".set_{method}_request({{metadata}}=True/False)"
                    for method in callee_methods
                ]
            )
            message = (
                f"[{', '.join([key for key in unrequested])}] are passed but are not"
                " explicitly set as requested or not requested for"
                f" {_routing_repr(self.owner)}.{self.method}, which is used within"
                f" {_routing_repr(parent)}.{caller}. Call `{_routing_repr(self.owner)}"
                + set_requests_on
                + "` for each metadata you want to request/ignore. See the"
                " Metadata Routing User guide"
                " <https://scikit-learn.org/stable/metadata_routing.html> for more"
                " information."
            )
            raise UnsetMetadataPassedError(
                message=message,
                unrequested_params=unrequested,
                routed_params=res,
            )
        return res