def _render_template(self, template_src, model, res_ids, engine='inline_template',
                         add_context=None, options=None):
        """ Render the given string on records designed by model / res_ids using
        the given rendering engine. Possible engine are small_web, qweb, or
        qweb_view.

        :param str template_src: template text to render or xml id of a qweb view;
        :param str model: model name of records on which we want to perform
          rendering (aka 'crm.lead');
        :param list res_ids: list of ids of records. All should belong to the
          Odoo model given by model;
        :param string engine: inline_template, qweb or qweb_view;

        :param dict add_context: additional context to give to renderer. It
          allows to add or update values to base rendering context generated
          by ``MailRenderMixin._render_<engine>_eval_context()``;
        :param dict options: options for rendering. Use in this method and also
          propagated to rendering sub-methods. May contain notably

            boolean post_process: perform a post processing on rendered result
            (notably html links management). See``_render_template_postprocess``;
            boolean preserve_comments: if set, comments are preserved. Default
            behavior is to remove them. It is used notably for browser-specific
            code implemented like comments;

        :returns: ``{res_id: string of rendered template based on record}``
        :rtype: dict
        """
        if options is None:
            options = {}

        if not isinstance(res_ids, (list, tuple)):
            raise ValueError(
                _('Template rendering should only be called with a list of IDs. Received “%(res_ids)s” instead.',
                  res_ids=res_ids)
            )
        if engine not in ('inline_template', 'qweb', 'qweb_view'):
            raise ValueError(
                _('Template rendering supports only inline_template, qweb, or qweb_view (view or raw); received %(engine)s instead.',
                  engine=engine)
            )
        valid_render_options = self._render_template_get_valid_options()
        if not set((options or {}).keys()) <= valid_render_options:
            raise ValueError(
                _('Those values are not supported as options when rendering: %(param_names)s',
                  param_names=', '.join(set(options.keys()) - valid_render_options)
                 )
            )

        if engine == 'qweb_view':
            rendered = self._render_template_qweb_view(template_src, model, res_ids,
                                                       add_context=add_context, options=options)
        elif engine == 'qweb':
            rendered = self._render_template_qweb(template_src, model, res_ids,
                                                  add_context=add_context, options=options)
        else:
            rendered = self._render_template_inline_template(template_src, model, res_ids,
                                                             add_context=add_context, options=options)

        if options.get('post_process'):
            rendered = self._render_template_postprocess(model, rendered)

        return rendered