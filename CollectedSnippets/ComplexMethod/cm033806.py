def _validate_required_if(self, terms, spec, context, module):
        if terms is None:
            return
        if not isinstance(terms, (list, tuple)):
            # This is already reported by schema checking
            return
        for check in terms:
            if not isinstance(check, (list, tuple)) or len(check) not in [3, 4]:
                # This is already reported by schema checking
                continue
            if len(check) == 4 and not isinstance(check[3], bool):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must have forth value omitted or of type bool; got %r" % (check[3], )
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-is_one_of-type',
                    msg=msg,
                )
            requirements = check[2]
            if not isinstance(requirements, (list, tuple)):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must have third value (requirements) being a list or tuple; got type %r" % (requirements, )
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-requirements-type',
                    msg=msg,
                )
                continue
            bad_term = False
            for term in requirements:
                if not isinstance(term, str):
                    msg = "required_if"
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " must have only strings in third value (requirements); got %r" % (term, )
                    self.reporter.error(
                        path=self.object_path,
                        code='required_if-requirements-type',
                        msg=msg,
                    )
                    bad_term = True
            if bad_term:
                continue
            if len(set(requirements)) != len(requirements):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " has repeated terms in requirements"
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-requirements-collision',
                    msg=msg,
                )
            if not set(requirements) <= set(spec):
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains terms in requirements which are not part of argument_spec: %s" % ", ".join(sorted(set(requirements).difference(set(spec))))
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-requirements-unknown',
                    msg=msg,
                )
            key = check[0]
            if key not in spec:
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " must have its key %s in argument_spec" % key
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-unknown-key',
                    msg=msg,
                )
                continue
            if key in requirements:
                msg = "required_if"
                if context:
                    msg += " found in %s" % " -> ".join(context)
                msg += " contains its key %s in requirements" % key
                self.reporter.error(
                    path=self.object_path,
                    code='required_if-key-in-requirements',
                    msg=msg,
                )
            value = check[1]
            if value is not None:
                _type = spec[key].get('type', 'str')
                if callable(_type):
                    _type_checker = _type
                else:
                    _type_checker = DEFAULT_TYPE_VALIDATORS.get(_type)
                try:
                    with CaptureStd():
                        dummy = _type_checker(value)
                except (Exception, SystemExit):
                    msg = "required_if"
                    if context:
                        msg += " found in %s" % " -> ".join(context)
                    msg += " has value %r which does not fit to %s's parameter type %r" % (value, key, _type)
                    self.reporter.error(
                        path=self.object_path,
                        code='required_if-value-type',
                        msg=msg,
                    )