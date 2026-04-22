def success(
        self,
        body: "SupportsStr",
        *,  # keyword-only args:
        icon: Optional[str] = None,
    ) -> "DeltaGenerator":
        """Display a success message.

        Parameters
        ----------
        body : str
            The success text to display.
        icon : None
            An optional parameter, that adds an emoji to the alert.
            The default is None.
            This argument can only be supplied by keyword.

        Example
        -------
        >>> st.success('This is a success message!', icon="✅")

        """
        alert_proto = AlertProto()
        alert_proto.body = clean_text(body)
        alert_proto.icon = validate_emoji(icon)
        alert_proto.format = AlertProto.SUCCESS
        return self.dg._enqueue("alert", alert_proto)