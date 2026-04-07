def render(self):
        """Render (thereby finalizing) the content of the response.

        If the content has already been rendered, this is a no-op.

        Return the baked response instance.
        """
        retval = self
        if not self._is_rendered:
            self.content = self.rendered_content
            for post_callback in self._post_render_callbacks:
                newretval = post_callback(retval)
                if newretval is not None:
                    retval = newretval
        return retval