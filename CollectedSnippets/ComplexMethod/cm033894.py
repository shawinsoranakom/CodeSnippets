def run(self, terms, variables=None, **kwargs):
        results = []

        if kwargs and not terms:
            # All of the necessary arguments can be provided as keywords, but we still need something to loop over
            terms = ['']

        for term in terms:
            try:
                # set defaults/global
                self.set_options(direct=kwargs)
                try:
                    if not self.parse_simple_args(term):
                        self.parse_kv_args(parse_kv(term))
                except AnsibleError:
                    raise
                except Exception as e:
                    raise AnsibleError("unknown error parsing with_sequence arguments: %r. Error was: %s" % (term, e))

                self.set_fields()
                if self.sanity_check():
                    results.extend(self.generate_sequence())

            except AnsibleError:
                raise
            except Exception as e:
                raise AnsibleError(
                    "unknown error generating sequence: %s" % e
                )

        return results