def error(
        self,
        body: "SupportsStr",
        *,  # keyword-only args:
        icon: Optional[str] = None,
    ) -> "DeltaGenerator":
        """Display error message.

        Parameters
        ----------
        icon : None
            An optional parameter, that adds an emoji to the alert.
            The default is None.
            This argument can only be supplied by keyword.
        body : str
            The error text to display.

        Example
        -------
        >>> st.error('This is an error', icon="🚨")

        """
        alert_proto = AlertProto()
        alert_proto.icon = validate_emoji(icon)
        alert_proto.body = clean_text(body)
        alert_proto.format = AlertProto.ERROR
        return self.dg._enqueue("alert", alert_proto)