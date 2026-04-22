def json(
        self,
        body: object,
        *,  # keyword-only arguments:
        expanded: bool = True,
    ) -> "DeltaGenerator":
        """Display object or string as a pretty-printed JSON string.

        Parameters
        ----------
        body : object or str
            The object to print as JSON. All referenced objects should be
            serializable to JSON as well. If object is a string, we assume it
            contains serialized JSON.

        expanded : bool
            An optional boolean that allows the user to set whether the initial
            state of this json element should be expanded. Defaults to True.
            This argument can only be supplied by keyword.

        Example
        -------
        >>> st.json({
        ...     'foo': 'bar',
        ...     'baz': 'boz',
        ...     'stuff': [
        ...         'stuff 1',
        ...         'stuff 2',
        ...         'stuff 3',
        ...         'stuff 5',
        ...     ],
        ... })

        .. output::
           https://doc-json.streamlitapp.com/
           height: 385px

        """
        import streamlit as st

        if isinstance(body, (SessionStateProxy, UserInfoProxy)):
            body = body.to_dict()

        if not isinstance(body, str):
            try:
                # Serialize body to string and try to interpret sets as lists
                body = json.dumps(body, default=_ensure_serialization)
            except TypeError as err:
                st.warning(
                    "Warning: this data structure was not fully serializable as "
                    f"JSON due to one or more unexpected keys.  (Error was: {err})"
                )
                body = json.dumps(body, skipkeys=True, default=_ensure_serialization)

        json_proto = JsonProto()
        json_proto.body = body
        json_proto.expanded = expanded
        return self.dg._enqueue("json", json_proto)