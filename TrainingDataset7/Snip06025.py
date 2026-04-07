def get_context_data(self, **kwargs):
        view = self.kwargs["view"]
        view_func = self._get_view_func(view)
        if view_func is None:
            raise Http404
        title, body, metadata = utils.parse_docstring(view_func.__doc__)
        title = title and utils.parse_rst(title, "view", _("view:") + view)
        body = body and utils.parse_rst(body, "view", _("view:") + view)
        for key in metadata:
            metadata[key] = utils.parse_rst(metadata[key], "model", _("view:") + view)
        return super().get_context_data(
            **{
                **kwargs,
                "name": view,
                "summary": strip_p_tags(title),
                "body": body,
                "meta": metadata,
            }
        )