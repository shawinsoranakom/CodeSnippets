async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete Habitica tasks."""
        if len(uids) > 1 and self.entity_description.key is HabiticaTodoList.TODOS:
            try:
                await self.coordinator.habitica.delete_completed_todos()
            except TooManyRequestsError as e:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="setup_rate_limit_exception",
                    translation_placeholders={"retry_after": str(e.retry_after)},
                ) from e
            except (HabiticaException, ClientError) as e:
                _LOGGER.debug(str(e))
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="delete_completed_todos_failed",
                ) from e
        else:
            for task_id in uids:
                try:
                    await self.coordinator.habitica.delete_task(UUID(task_id))
                except TooManyRequestsError as e:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="setup_rate_limit_exception",
                        translation_placeholders={"retry_after": str(e.retry_after)},
                    ) from e
                except (HabiticaException, ClientError) as e:
                    _LOGGER.debug(str(e))
                    raise ServiceValidationError(
                        translation_domain=DOMAIN,
                        translation_key=f"delete_{self.entity_description.key}_failed",
                    ) from e

        await self.coordinator.async_request_refresh()