def _test_docstring_params(self, method, doctree):
        doc_params, doc_types, doc_rtype = extract_docstring_params(doctree)

        signature = inspect.signature(method)
        sign_params = list(signature.parameters.values())
        sign_types = {param.name: param.annotation for param in sign_params}
        sign_rtype = signature.return_annotation

        if sign_rtype != signature.empty and doc_rtype != signature.empty:
            self.assertEqual(self._stringify_annotation(sign_rtype), doc_rtype)

        try:
            m = "the docstring is documenting non-existing parameters"
            self.assertGreaterEqual(set(sign_types), set(doc_params), m)
        except AssertionError:
            if sign_params[-1].kind != VAR_KEYWORD:
                raise
            # TODO: increase verbosity to warning
            logger.info(ABUSE_KWARGS.format(
                **self._subtest.params,
                function=signature,
                docstring=', '.join(tuple(doc_params)),
                func_missing=set(doc_params) - set(sign_types),
                doc_missing=(set(sign_types) - set(doc_params) - {
                  # self               , kwargs
                    sign_params[0].name, sign_params[-1].name}
                ) or {},
            ))

        for param, doc_type in doc_types.items():
            sign_type = sign_types.get(param, signature.empty)
            if sign_type != signature.empty:
                self.assertEqual(self._stringify_annotation(sign_type), doc_type)