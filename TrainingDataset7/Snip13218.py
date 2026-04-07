def render_annotated(self, context):
        """
        Return the given value.

        The default implementation of this method handles exceptions raised
        during rendering, which is not necessary for text nodes.
        """
        return self.s