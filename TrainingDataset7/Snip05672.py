def inline_formset_data(self):
        verbose_name = self.opts.verbose_name
        return json.dumps(
            {
                "name": "#%s" % self.formset.prefix,
                "options": {
                    "prefix": self.formset.prefix,
                    "addText": gettext("Add another %(verbose_name)s")
                    % {
                        "verbose_name": capfirst(verbose_name),
                    },
                    "deleteText": gettext("Remove"),
                },
            }
        )