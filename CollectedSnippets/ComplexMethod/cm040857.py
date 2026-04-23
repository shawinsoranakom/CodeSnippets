def _from_boto_response(self, response: Any, structure_shape: StructureShape) -> None:
        if not isinstance(response, dict):
            return

        if not isinstance(structure_shape, StructureShape):
            LOG.warning(
                "Step Functions could not normalise the response of integration '%s' due to the unexpected request template value of type '%s'",
                self.resource.resource_arn,
                type(structure_shape),
            )
            return

        shape_members = structure_shape.members
        response_bind_keys: list[str] = list(response.keys())
        for response_key in response_bind_keys:
            norm_response_key = self._to_sfn_cased(response_key)
            if response_key in shape_members:
                shape_member = shape_members[response_key]

                response_value = response.pop(response_key)
                response_value = self._from_boto_response_value(response_value)

                if isinstance(shape_member, StructureShape):
                    self._from_boto_response(response_value, shape_member)
                elif isinstance(shape_member, ListShape) and isinstance(response_value, list):
                    for response_value_member in response_value:
                        self._from_boto_response(response_value_member, shape_member.member)  # noqa

                response[norm_response_key] = response_value