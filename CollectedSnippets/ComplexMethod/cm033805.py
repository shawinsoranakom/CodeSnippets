def _validate_list_of_module_args(self, name, terms, spec, context):
        if terms is None:
            return
        if not isinstance(terms, (list, tuple)):
            # This is already reported by schema checking
            return
        for check in terms:
            if not isinstance(check, (list, tuple)):
                # This is already reported by schema checking
                continue
            bad_term = False
            for term in check:
                if not isinstance(term, str):
                    msg = name
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " must contain strings in the lists or tuples; found value %r" % (term, )
                    self.reporter.error(
                        path=self.object_path,
                        code=name + '-type',
                        msg=msg,
                    )
                    bad_term = True
            if bad_term:
                continue
            if len(set(check)) != len(check):
                msg = name
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has repeated terms"
                self.reporter.error(
                    path=self.object_path,
                    code=name + '-collision',
                    msg=msg,
                )
            if not set(check) <= set(spec):
                msg = name
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains terms which are not part of argument_spec: %s" % ", ".join(sorted(set(check).difference(set(spec))))
                self.reporter.error(
                    path=self.object_path,
                    code=name + '-unknown',
                    msg=msg,
                )