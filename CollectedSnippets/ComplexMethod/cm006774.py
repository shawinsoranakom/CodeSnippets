async def _get_default_model():
                    async with session_scope() as session:
                        variable_service = get_variable_service()
                        if variable_service is None:
                            return None, None
                        from langflow.services.variable.service import (
                            DatabaseVariableService,
                        )

                        if not isinstance(variable_service, DatabaseVariableService):
                            return None, None

                        # Variable names match those in the API
                        var_name = (
                            "__default_embedding_model__"
                            if model_type == "embeddings"
                            else "__default_language_model__"
                        )

                        try:
                            var = await variable_service.get_variable_object(
                                user_id=(
                                    UUID(component.user_id) if isinstance(component.user_id, str) else component.user_id
                                ),
                                name=var_name,
                                session=session,
                            )
                            if var and var.value:
                                parsed_value = json.loads(var.value)
                                if isinstance(parsed_value, dict):
                                    return parsed_value.get("model_name"), parsed_value.get("provider")
                        except (ValueError, json.JSONDecodeError, TypeError):
                            # Variable not found or invalid format
                            logger.info(
                                "Variable not found or invalid format: var_name=%s, user_id=%s, model_type=%s",
                                var_name,
                                component.user_id,
                                model_type,
                                exc_info=True,
                            )
                        return None, None