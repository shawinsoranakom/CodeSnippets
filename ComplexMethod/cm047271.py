def _generate_code(self, template: int | str | etree._Element):
        """ Compile the given template into a rendering function (generator)::

            render_template(qweb, values)

        This method can be called only by :meth:`_render` method or by
        the compiled code of t-call from an other template.

        An ``options`` dictionary is created and attached to the function.
        It contains rendering options that are part of the cache key in
        addition to template references.

        where ``qweb`` is a QWeb instance and ``values`` are the values to
        render.

        :returns: tuple containing code, options and main method name
        """
        if not isinstance(template, (int, str, etree._Element)):
            template = str(template)
        # The `compile_context`` dictionary includes the elements used for the
        # cache key to which are added the template references as well as
        # technical information useful for generating the function. This
        # dictionary is only used when compiling the template.
        compile_context = self.env.context.copy()

        try:
            element, document, ref = self._get_template(template)
        except (ValueError, UserError) as e:
            # return the error information if the template is not found or fail
            options = {k: compile_context.get(k, False) for k in self._get_template_cache_keys()}
            message = str(e)
            if hasattr(e, 'context') and e.context.get('view'):
                message = f"{message} (view: {e.context['view'].key})"
            options['error'] = (e.__class__, message, traceback.format_exc())
            return (None, options, 'not_found_template')

        compile_context.pop('raise_if_not_found', None)

        ref_name = element.attrib.pop('t-name', None)
        if isinstance(ref, int) or (isinstance(template, str) and '<' not in template):
            ref_name = self._get_template_info(ref)['key'] or ref_name

        # reference to get xml and etree (usually the template ID)
        compile_context['ref'] = ref
        # reference name or key to get xml and etree (usually the template XML ID)
        compile_context['ref_name'] = ref_name
        # str xml of the reference template used for compilation. Useful for debugging, dev mode and profiling.
        compile_context['ref_xml'] = str(document) if document else None
        # Identifier used to call `_compile`
        compile_context['template'] = template
        # Root of the etree which will be processed during compilation.
        compile_context['root'] = element.getroottree()
        # Reference to the last node being compiled. It is mainly used for debugging and displaying error messages.
        compile_context['_qweb_error_path_xml'] = compile_context.get('_qweb_error_path_xml', [None, None, None])

        compile_context['nsmap'] = {
            ns_prefix: str(ns_definition)
            for ns_prefix, ns_definition in compile_context.get('nsmap', {}).items()
        }

        # The options dictionary includes cache key elements and template
        # references. It will be attached to the generated function. This
        # dictionary is only there for logs, performance or test information.
        # The values of these `options` cannot be changed and must always be
        # identical in `context` and `self.env.context`.
        options = {
            key: compile_context.get(key, False)
            for key in self._get_template_cache_keys() + ['ref', 'ref_name']
        }

        # generate code
        ref_name = compile_context['ref_name'] or ''
        if isinstance(template, etree._Element):
            def_name = TO_VARNAME_REGEXP.sub(r'_', f'template_etree_{next(ETREE_TEMPLATE_REF)}')
        else:
            def_name = TO_VARNAME_REGEXP.sub(r'_', f'template_{ref_name if "<" not in ref_name else ""}_{ref}')

        name_gen = count()
        compile_context['make_name'] = lambda prefix: f"{def_name}_{prefix}_{next(name_gen)}"

        if element.text:
            element.text = FIRST_RSTRIP_REGEXP.sub(r'\2', element.text)

        compile_context['template_functions'] = {}

        compile_context['_text_concat'] = []
        self._append_text("", compile_context)  # To ensure the template function is a generator and doesn't become a regular function
        compile_context['template_functions'][f'{def_name}_content'] = (
            [f"def {def_name}_content(self, values):"]
            + self._compile_node(element, compile_context, 2)
            + self._flush_text(compile_context, 2, rstrip=True))

        compile_context['template_functions'][def_name] = [indent_code(f"""
            def {def_name}(self, values):
                if 'xmlid' not in values:
                    values['xmlid'] = {options['ref_name']!r}
                    values['viewid'] = {options['ref']!r}
                self.env.context['__qweb_loaded_functions'].update(template_functions)
                self.env.context['__qweb_loaded_options'][{options['ref']!r}] = self.env.context['__qweb_loaded_options'][{options['ref_name']!r}] = template_options
                self.env.context['__qweb_loaded_codes'][{options['ref']!r}] = self.env.context['__qweb_loaded_codes'][{options['ref_name']!r}] = code
                yield from {def_name}_content(self, values)
                """, 0)]

        code_lines = []
        code_lines.append(f'template_options = {pprint.pformat(options, indent=4)}')
        code_lines.append('code = None')
        code_lines.append('template_functions = {}')

        for lines in compile_context['template_functions'].values():
            code_lines.extend(lines)

        for name in compile_context['template_functions']:
            code_lines.append(f'template_functions[{name!r}] = {name}')

        code = '\n'.join(code_lines)

        if options.get('profile'):
            options['ref_xml'] = compile_context['ref_xml']

        return (code, options, def_name)