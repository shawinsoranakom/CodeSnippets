async def async_move_todo_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        """Move an item in the To-do list."""
        if TYPE_CHECKING:
            assert self.todo_items
        tasks_order = (
            self.coordinator.data.user.tasksOrder.todos
            if self.entity_description.key is HabiticaTodoList.TODOS
            else self.coordinator.data.user.tasksOrder.dailys
        )

        if previous_uid:
            pos = tasks_order.index(UUID(previous_uid))
            if pos < tasks_order.index(UUID(uid)):
                pos += 1

        else:
            pos = 0

        try:
            tasks_order[:] = (
                await self.coordinator.habitica.reorder_task(UUID(uid), pos)
            ).data
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
                translation_key=f"move_{self.entity_description.key}_item_failed",
                translation_placeholders={"pos": str(pos)},
            ) from e