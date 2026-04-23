def handle_result(
        self,
        event: Event[EventStateChangedData] | None,
        template: Template,
        last_result: str | TemplateError | None,
        result: str | TemplateError,
    ) -> None:
        """Handle a template result event callback."""
        if isinstance(result, TemplateError):
            _LOGGER.error(
                (
                    "TemplateError('%s') "
                    "while processing template '%s' "
                    "for attribute '%s' in entity '%s'"
                ),
                result,
                self.template,
                self._attribute,
                self._entity.entity_id,
            )
            if self.none_on_template_error:
                self._default_update(result)
            else:
                assert self.on_update
                self.on_update(result)
            return

        if not self.validator:
            assert self.on_update
            self.on_update(result)
            return

        try:
            validated = self.validator(result)
        except vol.Invalid as ex:
            _LOGGER.error(
                (
                    "Error validating template result '%s' "
                    "from template '%s' "
                    "for attribute '%s' in entity %s "
                    "validation message '%s'"
                ),
                result,
                self.template,
                self._attribute,
                self._entity.entity_id,
                ex.msg,
            )
            assert self.on_update
            self.on_update(None)
            return

        assert self.on_update
        self.on_update(validated)
        return