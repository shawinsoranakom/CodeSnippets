def snow(self) -> "DeltaGenerator":
        """Draw celebratory snowfall.

        Example
        -------
        >>> st.snow()

        ...then watch your app and get ready for a cool celebration!

        """
        snow_proto = SnowProto()
        snow_proto.show = True
        return self.dg._enqueue("snow", snow_proto)