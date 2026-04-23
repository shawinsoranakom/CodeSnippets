def _get_plugins_docs(self, plugin_type: str, names: collections.abc.Iterable[str], fail_ok: bool = False, fail_on_errors: bool = True) -> dict[str, dict]:
        loader = DocCLI._prep_loader(plugin_type)

        if plugin_type in ('filter', 'test'):
            jinja2_builtins = _jinja_plugins.get_jinja_builtin_plugin_descriptions(plugin_type)
            jinja2_builtins.update({name.split('.')[-1]: value for name, value in jinja2_builtins.items()})  # add short-named versions for lookup
        else:
            jinja2_builtins = {}

        # get the docs for plugins in the command line list
        plugin_docs = {}
        for plugin in names:
            doc: dict[str, t.Any] = {}
            try:
                doc, plainexamples, returndocs, metadata = self._get_plugin_docs_with_jinja2_builtins(
                    plugin,
                    plugin_type,
                    loader,
                    fragment_loader,
                    jinja2_builtins,
                )
            except AnsiblePluginNotFound as e:
                display.warning(to_native(e))
                continue
            except Exception as ex:
                msg = "Missing documentation (or could not parse documentation)"

                if not fail_on_errors:
                    plugin_docs[plugin] = {'error': f'{msg}: {ex}.'}
                    continue

                msg = f"{plugin_type} {plugin} {msg}"

                if fail_ok:
                    display.warning(f'{msg}: {ex}')
                else:
                    raise AnsibleError(f'{msg}.') from ex

            if not doc:
                # The doc section existed but was empty
                if not fail_on_errors:
                    plugin_docs[plugin] = {'error': 'No valid documentation found'}
                continue

            docs = DocCLI._combine_plugin_doc(plugin, plugin_type, doc, plainexamples, returndocs, metadata)
            if not fail_on_errors:
                # Check whether JSON serialization would break
                try:
                    _json.json_dumps_formatted(docs)
                except Exception as ex:  # pylint:disable=broad-except
                    plugin_docs[plugin] = {'error': f'Cannot serialize documentation as JSON: {ex}'}
                    continue

            plugin_docs[plugin] = docs

        return plugin_docs