def _get_values_500_error(cls, env, values, exception):
        values = super()._get_values_500_error(env, values, exception)
        if hasattr(exception, 'qweb'):
            qweb_error = exception.qweb
            exception_template = qweb_error.ref
            View = env["ir.ui.view"].sudo()
            view = exception_template and View._get_template_view(exception_template)
            if not view or qweb_error.element and qweb_error.element in view.arch:
                values['view'] = view
            else:
                # There might be 2 cases where the exception code can't be found
                # in the view, either the error is in a child view or the code
                # contains branding (<div t-att-data="request.browse('ok')"/>).
                et = view.with_context(inherit_branding=False)._get_combined_arch()
                node = et.xpath(qweb_error.path) if qweb_error.path else et
                line = node is not None and len(node) > 0 and etree.tostring(node[0], encoding='unicode')
                if line:
                    values['view'] = View._views_get(view.id).filtered(
                        lambda v: line in v.arch
                    )
                    values['view'] = values['view'] and values['view'][0]
        # Needed to show reset template on translated pages (`_prepare_environment` will set it for main lang)
        values['editable'] = request.env.uid and request.env.user.has_group('website.group_website_designer')
        return values