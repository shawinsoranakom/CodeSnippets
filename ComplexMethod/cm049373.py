def doc_model(self, model_name):
        """
        Get a complete listing of all the methods and fields for a
        specific model. The listing includes the htmlified docstring of
        the model, an enriched fields_get(), the methods signature,
        parameters and htmlified docstrings.

        It returns a json-serialized dictionnary with the following
        structure:

        .. code-block:: python

            {
                'model': str,
                'name': str,
                'doc': str | None,
                'fields': dict[str, dict],  # fields_get indexed by field name
                'methods': dict[str, dict],  # _doc_method indexed by method name
            }
        """
        if not self.env.user.has_group('api_doc.group_allow_doc'):
            raise AccessError(self.env._(
                "This page is only accessible to %s users.",
                self.env.ref('api_doc.group_allow_doc').sudo().name))
        if model_name not in self.env:
            raise NotFound()

        Model = self.env[model_name]
        Model.check_access('read')
        ir_model = self.env['ir.model']._get(model_name)

        # Client cache
        db_registry_sequence, _ = self.env.registry.get_sequences(self.env.cr)
        unique = hmac(
            self.env(su=True),
            scope='/doc/<model_name>.json',
            message=(
                db_registry_sequence,
                self.env.lang,
                sorted(self.env.user.all_group_ids.ids),
            ),
        )
        use_cache = not parse_cache_control_header(
            request.httprequest.headers.get('Cache-Control')).no_cache
        if use_cache and not is_resource_modified(request.httprequest.environ, etag=unique):
            return request.make_response('', status=HTTPStatus.NOT_MODIFIED)

        # No cache, generate the document and send it.
        result = {
            'model': model_name,
            'name': ir_model.name,
            'doc': None,  # TODO
            'fields': {
                field['name']: dict(
                    field,
                    module=next(iter(Model._fields[field['name']]._modules), None),
                )
                for field in Model.fields_get().values()
            },
            'methods': {
                method_name: self._doc_method(Model, model_name, method, method_name)
                for method_name in dir(Model)
                if (method := is_public_method(Model, method_name))
            },
        }

        response = request.make_json_response(result)
        response.headers['ETag'] = unique
        response.headers['Cache-Control'] = 'no-cache, private'  # no-chache != no-store
        response.headers['Content-Language'] = py_to_js_locale(self.env.lang)
        return response