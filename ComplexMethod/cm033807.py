def _validate_required_by(self, terms, spec, context):
        if terms is None:
            return
        if not isinstance(terms, Mapping):
            # This is already reported by schema checking
            return
        for key, value in terms.items():
            if isinstance(value, str):
                value = [value]
            if not isinstance(value, (list, tuple)):
                # This is already reported by schema checking
                continue
            for term in value:
                if not isinstance(term, str):
                    # This is already reported by schema checking
                    continue
            if len(set(value)) != len(value) or key in value:
                msg = "required_by"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has repeated terms"
                self.reporter.error(
                    path=self.object_path,
                    code='required_by-collision',
                    msg=msg,
                )
            if not set(value) <= set(spec) or key not in spec:
                msg = "required_by"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains terms which are not part of argument_spec: %s" % ", ".join(sorted(set(value).difference(set(spec))))
                self.reporter.error(
                    path=self.object_path,
                    code='required_by-unknown',
                    msg=msg,
                )