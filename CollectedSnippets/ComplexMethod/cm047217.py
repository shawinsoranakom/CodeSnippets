def test_form_new_record(self):
        allowed_models = set(self.env['ir.model.access']._get_allowed_models('create'))
        allowed_models -= IGNORE_MODEL_NAMES_NEW_FORM

        for model_name, model in self.env.items():
            if (
                model._abstract
                or model._transient
                or not model._auto
                or model_name not in allowed_models
            ):
                continue

            default_form_id = self.env['ir.ui.view'].default_view(model_name, 'form')
            if not default_form_id:
                continue

            default_form = self.env['ir.ui.view'].browse(default_form_id)
            if not default_form.arch:
                continue
            view_elem = etree.fromstring(default_form.arch)
            if view_elem.get('create') in ('0', 'false'):
                continue

            with self.subTest(
                msg="Create a new record from form view doesn't work (first onchange call).",
                model=model_name,
            ), contextlib.suppress(UserError):
                # Test to open the Form view to check first onchange
                Form(model)