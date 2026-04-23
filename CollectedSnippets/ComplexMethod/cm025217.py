def check_current_user(
            hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
        ) -> None:
            """Check current user."""

            def output_error(message_id: str, message: str) -> None:
                """Output error message."""
                connection.send_message(
                    messages.error_message(msg["id"], message_id, message)
                )

            if only_owner and not connection.user.is_owner:
                output_error("only_owner", "Only allowed as owner")
                return None

            if only_system_user and not connection.user.system_generated:
                output_error("only_system_user", "Only allowed as system user")
                return None

            if not allow_system_user and connection.user.system_generated:
                output_error("not_system_user", "Not allowed as system user")
                return None

            if only_active_user and not connection.user.is_active:
                output_error("only_active_user", "Only allowed as active user")
                return None

            if only_inactive_user and connection.user.is_active:
                output_error("only_inactive_user", "Not allowed as active user")
                return None

            if only_supervisor and connection.user.name != HASSIO_USER_NAME:
                output_error("only_supervisor", "Only allowed as Supervisor")
                return None

            return func(hass, connection, msg)