def _get_subpackage_search_paths(self, candidate_paths):
        collection_name = '.'.join(self._split_name[1:3])
        collection_meta = _get_collection_metadata(collection_name)

        # check for explicit redirection, as well as ancestor package-level redirection (only load the actual code once!)
        redirect = None
        explicit_redirect = False

        routing_entry = _nested_dict_get(collection_meta, ['import_redirection', self._fullname])
        if routing_entry:
            redirect = routing_entry.get('redirect')

        if redirect:
            explicit_redirect = True
        else:
            redirect = _get_ancestor_redirect(self._redirected_package_map, self._fullname)

        # NB: package level redirection requires hooking all future imports beneath the redirected source package
        # in order to ensure sanity on future relative imports. We always import everything under its "real" name,
        # then add a sys.modules entry with the redirected name using the same module instance. If we naively imported
        # the source for each redirection, most submodules would import OK, but we'd have N runtime copies of the module
        # (one for each name), and relative imports that ascend above the redirected package would break (since they'd
        # see the redirected ancestor package contents instead of the package where they actually live).
        if redirect:
            # FIXME: wrap this so we can be explicit about a failed redirection
            self._redirect_module = import_module(redirect)
            if explicit_redirect and hasattr(self._redirect_module, '__path__') and self._redirect_module.__path__:
                # if the import target looks like a package, store its name so we can rewrite future descendent loads
                self._redirected_package_map[self._fullname] = redirect

            # if we redirected, don't do any further custom package logic
            return None

        # we're not doing a redirect- try to find what we need to actually load a module/package

        # this will raise ImportError if we can't find the requested module/package at all
        if not candidate_paths:
            # noplace to look, just ImportError
            raise ImportError('package has no paths')

        found_path, has_code, package_path = self._module_file_from_path(self._package_to_load, candidate_paths[0])

        # still here? we found something to load...
        if has_code:
            self._source_code_path = found_path

        if package_path:
            return [package_path]  # always needs to be a list

        return None