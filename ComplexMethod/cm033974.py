def _dump_results(
        self,
        result: _c.Mapping[str, t.Any],
        indent: int | None = None,
        sort_keys: bool = True,
        keep_invocation: bool = False,
        serialize: bool = True,
    ) -> str:
        try:
            result_format = self.get_option('result_format')
        except KeyError:
            # Callback does not declare result_format nor extend result_format_callback
            result_format = 'json'

        try:
            pretty_results = self.get_option('pretty_results')
        except KeyError:
            # Callback does not declare pretty_results nor extend result_format_callback
            pretty_results = None

        indent_conditions = (
            result.get('_ansible_verbose_always'),
            pretty_results is None and result_format != 'json',
            pretty_results is True,
            self._display.verbosity > 2,
        )

        if not indent and any(indent_conditions):
            try:
                indent = self.get_option('result_indentation')
            except KeyError:
                # Callback does not declare result_indentation nor extend result_format_callback
                indent = 4
        if pretty_results is False:
            # pretty_results=False overrides any specified indentation
            indent = None

        # All result keys stating with _ansible_ are internal, so remove them from the result before we output anything.
        abridged_result = strip_internal_keys(module_response_deepcopy(result))

        # remove invocation unless specifically wanting it
        if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
            del abridged_result['invocation']

        # remove diff information from screen output
        if self._display.verbosity < 3 and 'diff' in result:
            del abridged_result['diff']

        # remove error/warning values; the stdout callback should have already handled them
        abridged_result.pop('exception', None)
        abridged_result.pop('warnings', None)
        abridged_result.pop('deprecations', None)

        abridged_result = _engine.TemplateEngine().transform(abridged_result)  # ensure the dumped view matches the transformed view a playbook sees

        if not serialize:
            # Just return ``abridged_result`` without going through serialization
            # to permit callbacks to take advantage of ``_dump_results``
            # that want to further modify the result, or use custom serialization
            return abridged_result

        if result_format == 'json':
            return json.dumps(abridged_result, cls=_fallback_to_str.Encoder, indent=indent, ensure_ascii=False, sort_keys=sort_keys)

        if result_format == 'yaml':
            # None is a sentinel in this case that indicates default behavior
            # default behavior for yaml is to prettify results
            lossy = pretty_results in (None, True)
            if lossy:
                # if we already have stdout, we don't need stdout_lines
                if 'stdout' in abridged_result and 'stdout_lines' in abridged_result:
                    abridged_result['stdout_lines'] = '<omitted>'

                # if we already have stderr, we don't need stderr_lines
                if 'stderr' in abridged_result and 'stderr_lines' in abridged_result:
                    abridged_result['stderr_lines'] = '<omitted>'

            return '\n%s' % textwrap.indent(
                yaml.dump(
                    abridged_result,
                    allow_unicode=True,
                    Dumper=functools.partial(_AnsibleCallbackDumper, lossy=lossy),
                    default_flow_style=False,
                    indent=indent,
                    width=self._get_yaml_width(),
                    # sort_keys=sort_keys  # This requires PyYAML>=5.1
                ),
                ' ' * (indent or 4)
            )

        # DTFIX5: add test to exercise this case
        raise ValueError(f'Unsupported result_format {result_format!r}.')