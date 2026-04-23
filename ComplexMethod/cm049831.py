def _render_field(self, field, res_ids, engine='inline_template',
                      # lang options
                      compute_lang=False, res_ids_lang=False, set_lang=False,
                      # rendering context and options
                      add_context=None, options=None):
        """ Given some record ids, render a template located on field on all
        records. ``field`` should be a field of self (i.e. ``body_html`` on
        ``mail.template``). res_ids are record IDs linked to ``model`` field
        on self.

        :param field: a field name existing on self;
        :param list res_ids: list of ids of records (all belonging to same model
          defined by ``self.render_model``)
        :param string engine: inline_template, qweb, or qweb_view;

        :param boolean compute_lang: compute language to render on translated
          version of the template instead of default (probably english) one.
          Language will be computed based on ``self.lang``;
        :param dict res_ids_lang: record id to lang, e.g. already rendered
          using another way;
        :param string set_lang: force language for rendering. It should be a
          valid lang code matching an activate res.lang. Checked only if
          ``compute_lang`` is False;

        :param dict add_context: additional context to give to renderer;
        :param dict options: options for rendering. Use in this method and also
          propagated to rendering sub-methods. Base values come from the field
          (coming from ``render_options`` parameter) and are updated by this
          optional dictionary. May contain notably

            boolean post_process: perform a post processing on rendered result
            (notably html links management). See``_render_template_postprocess``;
            boolean preserve_comments: if set, comments are preserved. Default
            behavior is to remove them. It is used notably for browser-specific
            code implemented like comments;

        :return: {res_id: string of rendered template based on record}
        :rtype: dict
        """
        if field not in self:
            raise ValueError(
                _('Rendering of %(field_name)s is not possible as not defined on template.',
                  field_name=field
                 )
            )
        self.ensure_one()
        if compute_lang:
            templates_res_ids = self._classify_per_lang(res_ids)
        elif res_ids_lang:
            templates_res_ids = {}
            for res_id, lang in res_ids_lang.items():
                lang_values = templates_res_ids.setdefault(lang, (self.with_context(lang=lang), []))
                lang_values[1].append(res_id)
        elif set_lang:
            templates_res_ids = {set_lang: (self.with_context(lang=set_lang), res_ids)}
        else:
            templates_res_ids = {self.env.context.get('lang'): (self, res_ids)}

        # rendering options (update default defined on field by asked options)
        f = self._fields[field]
        if hasattr(f, 'render_engine') and f.render_engine:
            engine = f.render_engine

        render_options = options.copy() if options else {}
        if hasattr(f, 'render_options') and f.render_options:
            render_options = {**f.render_options, **render_options}

        return {
            res_id: rendered
            for (template, tpl_res_ids) in templates_res_ids.values()
            for res_id, rendered in template._render_template(
                template[field],
                template.render_model,
                tpl_res_ids,
                engine=engine,
                add_context=add_context,
                options=render_options,
            ).items()
        }