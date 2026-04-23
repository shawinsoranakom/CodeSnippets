def copy(self, default=None):
        new_boms = super().copy(default)
        for old_bom, new_bom in zip(self, new_boms):
            if old_bom.operation_ids:
                operations_mapping = {}
                for original, copied in zip(old_bom.operation_ids, new_bom.operation_ids.sorted()):
                    operations_mapping[original] = copied
                for bom_line in new_bom.bom_line_ids:
                    if bom_line.operation_id:
                        bom_line.operation_id = operations_mapping[bom_line.operation_id]
                for byproduct in new_bom.byproduct_ids:
                    if byproduct.operation_id:
                        byproduct.operation_id = operations_mapping[byproduct.operation_id]
                for operation in old_bom.operation_ids:
                    if operation.blocked_by_operation_ids:
                        copied_operation = operations_mapping[operation]
                        dependencies = []
                        for dependency in operation.blocked_by_operation_ids:
                            dependencies.append(Command.link(operations_mapping[dependency].id))
                        copied_operation.blocked_by_operation_ids = dependencies
        return new_boms