def balloons(self) -> "DeltaGenerator":
        """Draw celebratory balloons.

        Example
        -------
        >>> st.balloons()

        ...then watch your app and get ready for a celebration!

        """
        balloons_proto = BalloonsProto()
        balloons_proto.show = True
        return self.dg._enqueue("balloons", balloons_proto)