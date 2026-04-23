def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:
            term_file = os.path.basename(term)
            found_paths = []
            if term_file != term:
                found_paths.append(self.find_file_in_search_path(variables, 'files', os.path.dirname(term)))
            else:
                # no dir, just file, so use paths and 'files' paths instead
                if 'ansible_search_path' in variables:
                    paths = variables['ansible_search_path']
                else:
                    paths = [self.get_basedir(variables)]
                for p in paths:
                    found_paths.append(os.path.join(p, 'files'))
                    found_paths.append(p)

            for dwimmed_path in found_paths:
                if dwimmed_path:
                    globbed = glob.glob(to_bytes(os.path.join(dwimmed_path, term_file), errors='surrogate_or_strict'))
                    term_results = [to_text(g, errors='surrogate_or_strict') for g in globbed if os.path.isfile(g)]
                    if term_results:
                        ret.extend(term_results)
                        break
        return ret