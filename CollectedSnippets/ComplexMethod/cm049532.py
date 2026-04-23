def _check_valid_and_existing_paths(self):
        """ Verify that the paths exist and are valid.

        :return: None
        :raises: ValidationError if at least one of the paths isn't valid.
        """
        name_pattern = re.compile(r'^(\w|-|\.)+$')
        for form_field in self.filtered('path'):
            if not re.match(name_pattern, form_field.path):
                raise ValidationError(_(
                    "Invalid path %(path)s. It should only contain alphanumerics, hyphens,"
                    " underscores or points.",
                    path=form_field.path,
                ))

            path = form_field.path.split('.')
            is_header_footer = form_field.document_type == 'quotation_document'
            Model = self.env['sale.order'] if is_header_footer else self.env['sale.order.line']
            for i in range(len(path)):
                field_name = path[i]
                if Model == []:
                    raise ValidationError(_(
                        "Please use only relational fields until the last value of your path."
                    ))
                if field_name not in Model._fields:
                    raise ValidationError(_(
                        "The field %(field_name)s doesn't exist on model %(model_name)s",
                        field_name=field_name,
                        model_name=Model._name
                    ))
                if i != len(path) - 1:
                    Model = Model.mapped(field_name)