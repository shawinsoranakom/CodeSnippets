def _compile(self, template):
        ref = None
        if isinstance(template, str) and template.endswith('.xml'):
            module_path = Manifest.for_addon(Path(template).parts[0]).path
            if 'templates' not in Path(file_path(template)).relative_to(module_path).parts:
                raise ValueError("The templates file %s must be under a subfolder 'templates' of a module", template)
            else:
                with file_open(template, 'rb', filter_ext=('.xml',)) as file:
                    template = etree.fromstring(file.read())
        elif not isinstance(template, etree._Element):
            ref = self._get_template_info(template)['id']

        if ref:
            template_functions, def_name, options = self._generate_code_cached(ref)
        else:
            template_functions, def_name, options = self._generate_code_uncached(template)

        render_template = template_functions[def_name]
        if options.get('profile') and render_template.__name__ != 'profiled_method_compile':
            ref = options.get('ref')
            ref_xml = str(val) if (val := options.get('ref_xml')) else None

            def wrap(function):
                def profiled_method_compile(self, values):
                    qweb_tracker = QwebTracker(ref, ref_xml, self.env.cr)
                    self = self.with_context(qweb_tracker=qweb_tracker)
                    if qweb_tracker.execution_context_enabled:
                        with ExecutionContext(template=ref):
                            return function(self, values)
                    return function(self, values)

                return profiled_method_compile

            for key, function in template_functions.items():
                if isinstance(function, FunctionType):
                    template_functions[key] = wrap(function)

        return (template_functions, def_name, options)