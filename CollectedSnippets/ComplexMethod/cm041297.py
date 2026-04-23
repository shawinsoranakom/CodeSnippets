def render_vtl(self, template: str, variables: dict, as_json=False) -> str | dict:
        """
        Render the given VTL template against the dict of variables. Note that this is a
        potentially mutating operation which may change the values of `variables` in-place.
        :param template: the template string
        :param variables: dict of variables available to the template
        :param as_json: whether to return the result as parsed JSON dict
        :return: the rendered template string value (or dict)
        """
        if variables is None:
            variables = {}

        if not template:
            return template

        # fix "#set" commands
        template = re.sub(r"(^|\n)#\s+set(.*)", r"\1#set\2", template, count=re.MULTILINE)

        # enable syntax like "test#${foo.bar}"
        empty_placeholder = " __pLaCe-HoLdEr__ "
        template = re.sub(
            r"([^\s]+)#\$({)?(.*)",
            rf"\1#{empty_placeholder}$\2\3",
            template,
            count=re.MULTILINE,
        )

        # add extensions for common string functions below

        class ExtendedString(str):
            def toString(self, *_, **__):
                return self

            def trim(self, *args, **kwargs):
                return ExtendedString(self.strip(*args, **kwargs))

            def toLowerCase(self, *_, **__):
                return ExtendedString(self.lower())

            def toUpperCase(self, *_, **__):
                return ExtendedString(self.upper())

            def contains(self, *args):
                return self.find(*args) >= 0

            def replaceAll(self, regex, replacement):
                escaped_replacement = replacement.replace("$", "\\")
                return ExtendedString(re.sub(regex, escaped_replacement, self))

        def apply(obj, **_):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        obj[k] = ExtendedString(v)
            return obj

        # loop through the variables and enable certain additional util functions (e.g., string utils)
        variables = {} if variables is None else variables
        recurse_object(variables, apply)

        # prepare and render template
        t = airspeed.Template(template)
        namespace = self.prepare_namespace(variables)

        # this steps prepares the namespace for object traversal,
        # e.g, foo.bar.trim().toLowerCase().replace
        input_var = variables.get("input") or {}
        dict_pack = input_var.get("body")
        if isinstance(dict_pack, dict):
            for k, v in dict_pack.items():
                namespace.update({k: v})

        rendered_template = t.merge(namespace)

        # revert temporary changes from the fixes above
        rendered_template = rendered_template.replace(empty_placeholder, "")

        if as_json:
            rendered_template = json.loads(rendered_template)
        return rendered_template