def _should_check_constraints(self, connection):
        return (
            connection.features.can_defer_constraint_checks
            and not connection.needs_rollback
            and connection.is_usable()
        )