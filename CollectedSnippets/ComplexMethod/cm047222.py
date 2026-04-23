def check_filter(self, name, model, domain, aggregates, groupby, order, context):
        if groupby:
            try:
                Model = self.env[model].with_context(context)
                groupby = [groupby] if isinstance(groupby, str) else groupby
                groupby = [
                    f"{group_spec}:month" if (
                        ":" not in group_spec and
                        group_spec in Model._fields and
                        Model._fields[group_spec].type in ('date, datetime')
                    ) else group_spec
                    for group_spec in groupby
                ]
                Model.formatted_read_group(domain, groupby, aggregates, order=order)
            except ValueError as e:
                raise self.failureException("Test filter '%s' failed: %s" % (name, e)) from None
            except KeyError as e:
                raise self.failureException("Test filter '%s' failed: field or aggregate %s does not exist"% (name, e)) from None
        elif domain:
            try:
                self.env[model].with_context(context).search(domain, order=order)
            except ValueError as e:
                raise self.failureException("Test filter '%s' failed: %s" % (name, e)) from None
        else:
            _logger.info("No domain or group by in filter %s with model %s and context %s", name, model, context)