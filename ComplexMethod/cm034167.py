def post_validate_attribute(self, name: str, *, templar: TemplateEngine):
        attribute: FieldAttribute = self.fattributes[name]

        # DTFIX-FUTURE: this can probably be used in many getattr cases below, but the value may be out-of-date in some cases
        original_value = getattr(self, name)  # we save this original (likely Origin-tagged) value to pass as `obj` for errors

        if attribute.static:
            value = getattr(self, name)

            # we don't template 'vars' but allow template as values for later use
            if name not in ('vars',) and templar.is_template(value):
                display.warning('"%s" is not templatable, but we found: %s, '
                                'it will not be templated and will be used "as is".' % (name, value))
            return Sentinel

        if getattr(self, name) is None:
            if not attribute.required:
                return Sentinel

            raise AnsibleFieldAttributeError(f'The field {name!r} is required but was not set.', obj=self.get_ds())

        from .role_include import IncludeRole

        if not attribute.always_post_validate and isinstance(self, IncludeRole) and self.statically_loaded:  # import_role
            # normal field attributes should not go through post validation on import_role/import_tasks
            # only import_role is checked here because import_tasks never reaches this point
            return Sentinel

        # Skip post validation unless always_post_validate is True, or the object requires post validation.
        if not attribute.always_post_validate and not self._post_validate_object:
            # Intermediate objects like Play() won't have their fields validated by
            # default, as their values are often inherited by other objects and validated
            # later, so we don't want them to fail out early
            return Sentinel

        try:
            # Run the post-validator if present. These methods are responsible for
            # using the given templar to template the values, if required.
            method = getattr(self, '_post_validate_%s' % name, None)

            if method:
                value = method(attribute, getattr(self, name), templar)
            elif attribute.isa == 'class':
                value = getattr(self, name)
            else:
                try:
                    # if the attribute contains a variable, template it now
                    value = templar.template(getattr(self, name))
                except AnsibleValueOmittedError:
                    # If this evaluated to the omit value, set the value back to inherited by context
                    # or default specified in the FieldAttribute and move on
                    value = self.set_to_context(name)

                    if value is Sentinel:
                        return value

            # and make sure the attribute is of the type it should be
            if value is not None:
                value = self.get_validated_value(name, attribute, value, templar)

            # returning the value results in assigning the massaged value back to the attribute field
            return value
        except Exception as ex:
            if name == 'args':
                raise  # no useful information to contribute, raise the original exception

            raise AnsibleFieldAttributeError(f'Error processing keyword {name!r}.', obj=original_value) from ex