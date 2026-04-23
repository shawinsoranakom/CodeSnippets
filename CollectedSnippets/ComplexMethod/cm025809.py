async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a Habitica todo."""
        refresh_required = False
        current_item = next(
            (task for task in (self.todo_items or []) if task.uid == item.uid),
            None,
        )

        if TYPE_CHECKING:
            assert item.uid
            assert current_item
            assert item.summary

        task = Task(
            text=item.summary,
            notes=item.description or "",
        )

        if (
            self.entity_description.key is HabiticaTodoList.TODOS
        ):  # Only todos support a due date.
            task["date"] = item.due

        if (
            item.summary != current_item.summary
            or item.description != current_item.description
            or item.due != current_item.due
        ):
            try:
                await self.coordinator.habitica.update_task(UUID(item.uid), task)
                refresh_required = True
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
                    translation_key=f"update_{self.entity_description.key}_item_failed",
                    translation_placeholders={"name": item.summary or ""},
                ) from e

        try:
            # Score up or down if item status changed
            if (
                current_item.status is TodoItemStatus.NEEDS_ACTION
                and item.status == TodoItemStatus.COMPLETED
            ):
                score_result = await self.coordinator.habitica.update_score(
                    UUID(item.uid), Direction.UP
                )
                refresh_required = True
            elif (
                current_item.status is TodoItemStatus.COMPLETED
                and item.status == TodoItemStatus.NEEDS_ACTION
            ):
                score_result = await self.coordinator.habitica.update_score(
                    UUID(item.uid), Direction.DOWN
                )
                refresh_required = True
            else:
                score_result = None
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
                translation_key=f"score_{self.entity_description.key}_item_failed",
                translation_placeholders={"name": item.summary or ""},
            ) from e

        if score_result and score_result.data.tmp.drop.key:
            drop = score_result.data.tmp.drop
            msg = (
                f"![{drop.key}]({ASSETS_URL}Pet_{drop.Type}_{drop.key}.png)\n"
                f"{drop.dialog}"
            )
            persistent_notification.async_create(
                self.hass, message=msg, title="Habitica"
            )
        if refresh_required:
            await self.coordinator.async_request_refresh()