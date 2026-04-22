def info(
        self,
        body: "SupportsStr",
        *,  # keyword-only args:
        icon: Optional[str] = None,
    ) -> "DeltaGenerator":
        """Display an informational message.

        Parameters
        ----------
        body : str
            The info text to display.
        icon : None
            An optional parameter, that adds an emoji to the alert.
            The default is None.
            This argument can only be supplied by keyword.

        Example
        -------
        >>> st.info('This is a purely informational message', icon="ℹ️")

        """

        alert_proto = AlertProto()
        alert_proto.body = clean_text(body)
        alert_proto.icon = validate_emoji(icon)
        alert_proto.format = AlertProto.INFO
        return self.dg._enqueue("alert", alert_proto)