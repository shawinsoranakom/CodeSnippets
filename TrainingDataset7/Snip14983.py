def render_to_response(self, context, **response_kwargs):
        def indent(s):
            return s.replace("\n", "\n  ")

        with builtin_template_path("i18n_catalog.js").open(encoding="utf-8") as fh:
            template = Engine().from_string(fh.read())
        context["catalog_str"] = (
            indent(json.dumps(context["catalog"], sort_keys=True, indent=2))
            if context["catalog"]
            else None
        )
        context["formats_str"] = indent(
            json.dumps(context["formats"], sort_keys=True, indent=2)
        )

        return HttpResponse(
            template.render(Context(context)), 'text/javascript; charset="utf-8"'
        )