def _get_loader(self, fullname, path=None):
            # type: (RestrictedModuleLoader, str, list[str]) -> RestrictedModuleLoader | None
            """Return self if the given fullname is restricted, otherwise return None."""
            if fullname in self.loaded_modules:
                return None  # ignore modules that are already being loaded

            if is_name_in_namepace(fullname, ['ansible']):
                if not self.restrict_to_module_paths:
                    return None  # for non-modules, everything in the ansible namespace is allowed

                if fullname in ('ansible.module_utils.basic',):
                    return self  # intercept loading so we can modify the result

                if is_name_in_namepace(fullname, ['ansible.module_utils', self.name]):
                    return None  # module_utils and module under test are always allowed

                if any(os.path.exists(candidate_path) for candidate_path in convert_ansible_name_to_absolute_paths(fullname)):
                    return self  # restrict access to ansible files that exist

                return None  # ansible file does not exist, do not restrict access

            if is_name_in_namepace(fullname, ['ansible_collections']):
                if not collection_loader:
                    return self  # restrict access to collections when we are not testing a collection

                if not self.restrict_to_module_paths:
                    return None  # for non-modules, everything in the ansible namespace is allowed

                if is_name_in_namepace(fullname, ['ansible_collections...plugins.module_utils', self.name]):
                    return None  # module_utils and module under test are always allowed

                if collection_loader.find_module(fullname, path):
                    return self  # restrict access to collection files that exist

                return None  # collection file does not exist, do not restrict access

            # not a namespace we care about
            return None