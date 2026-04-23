def check_dependency(self, operation, dependency):
        """
        Return True if the given operation depends on the given dependency,
        False otherwise.
        """
        # Created model
        if (
            dependency.field_name is None
            and dependency.type == OperationDependency.Type.CREATE
        ):
            return (
                isinstance(operation, operations.CreateModel)
                and operation.name_lower == dependency.model_name_lower
            )
        # Created field
        elif (
            dependency.field_name is not None
            and dependency.type == OperationDependency.Type.CREATE
        ):
            return (
                isinstance(operation, operations.CreateModel)
                and operation.name_lower == dependency.model_name_lower
                and any(dependency.field_name == x for x, y in operation.fields)
            ) or (
                isinstance(operation, operations.AddField)
                and operation.model_name_lower == dependency.model_name_lower
                and operation.name_lower == dependency.field_name_lower
            )
        # Removed field
        elif (
            dependency.field_name is not None
            and dependency.type == OperationDependency.Type.REMOVE
        ):
            return (
                isinstance(operation, operations.RemoveField)
                and operation.model_name_lower == dependency.model_name_lower
                and operation.name_lower == dependency.field_name_lower
            )
        # Removed model
        elif (
            dependency.field_name is None
            and dependency.type == OperationDependency.Type.REMOVE
        ):
            return (
                isinstance(operation, operations.DeleteModel)
                and operation.name_lower == dependency.model_name_lower
            )
        # Field being altered
        elif (
            dependency.field_name is not None
            and dependency.type == OperationDependency.Type.ALTER
        ):
            return (
                isinstance(operation, operations.AlterField)
                and operation.model_name_lower == dependency.model_name_lower
                and operation.name_lower == dependency.field_name_lower
            )
        # order_with_respect_to being unset for a field
        elif (
            dependency.field_name is not None
            and dependency.type == OperationDependency.Type.REMOVE_ORDER_WRT
        ):
            return (
                isinstance(operation, operations.AlterOrderWithRespectTo)
                and operation.name_lower == dependency.model_name_lower
                and (operation.order_with_respect_to or "").lower()
                != dependency.field_name_lower
            )
        # Field is removed and part of an index/unique_together
        elif (
            dependency.field_name is not None
            and dependency.type == OperationDependency.Type.ALTER_FOO_TOGETHER
        ):
            return (
                isinstance(
                    operation,
                    (operations.AlterUniqueTogether, operations.AlterIndexTogether),
                )
                and operation.name_lower == dependency.model_name_lower
            )
        # Field is removed and part of an index/constraint.
        elif (
            dependency.field_name is not None
            and dependency.type == OperationDependency.Type.REMOVE_INDEX_OR_CONSTRAINT
        ):
            return (
                isinstance(
                    operation,
                    (operations.RemoveIndex, operations.RemoveConstraint),
                )
                and operation.model_name_lower == dependency.model_name_lower
            )
        # Unknown dependency. Raise an error.
        else:
            raise ValueError("Can't handle dependency %r" % (dependency,))