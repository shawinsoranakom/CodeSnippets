def modify_nullable(conn, inspector, table_name, upgrade=True):
    columns = inspector.get_columns(table_name)
    nullable_changes = {"apikey": {"created_at": False}, "variable": {"created_at": True, "updated_at": True}}

    if table_name in columns:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            for column_name, nullable_setting in nullable_changes.get(table_name, {}).items():
                column_info = next((col for col in columns if col["name"] == column_name), None)
                if column_info:
                    current_nullable = column_info["nullable"]
                    target_nullable = nullable_setting if upgrade else not nullable_setting

                    if current_nullable != target_nullable:
                        batch_op.alter_column(
                            column_name, existing_type=sa.DateTime(timezone=True), nullable=target_nullable
                        )
                    else:
                        logger.info(
                            f"Column '{column_name}' in table '{table_name}' already has nullable={target_nullable}"
                        )
                else:
                    logger.warning(f"Column '{column_name}' not found in table '{table_name}'")