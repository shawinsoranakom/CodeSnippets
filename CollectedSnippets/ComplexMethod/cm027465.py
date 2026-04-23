def _update(self) -> None:
        """Retrieve sensor data from the query."""
        data = None
        self._attr_extra_state_attributes = {}
        sess: scoped_session = self.sessionmaker()
        try:
            rendered_query = check_and_render_sql_query(self.hass, self._query)
            _lambda_stmt = generate_lambda_stmt(rendered_query)
            result: Result = sess.execute(_lambda_stmt)
        except (TemplateError, InvalidSqlQuery) as err:
            _LOGGER.error(
                "Error rendering query %s: %s",
                redact_credentials(self._query.template),
                redact_credentials(str(err)),
            )
            sess.rollback()
            sess.close()
            return
        except SQLAlchemyError as err:
            _LOGGER.error(
                "Error executing query %s: %s",
                rendered_query,
                redact_credentials(str(err)),
            )
            sess.rollback()
            sess.close()
            return

        for res in result.mappings():
            _LOGGER.debug("Query %s result in %s", rendered_query, res.items())
            data = res[self._column_name]
            for key, value in res.items():
                self._attr_extra_state_attributes[key] = convert_value(value)

        if data is not None and isinstance(data, (bytes, bytearray)):
            data = f"0x{data.hex()}"

        if data is not None and self._template is not None:
            variables = self._template_variables_with_value(data)
            if self._render_availability_template(variables):
                _value = self._template.async_render_as_value_template(
                    self.entity_id, variables, None
                )
                self._set_native_value_with_possible_timestamp(_value)
                self._process_manual_data(variables)
        else:
            self._attr_native_value = data

        if data is None:
            _LOGGER.warning("%s returned no results", rendered_query)

        sess.close()