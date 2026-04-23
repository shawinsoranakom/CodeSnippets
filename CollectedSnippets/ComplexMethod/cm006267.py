def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)  # type: ignore
    flow_columns = {column["name"] for column in inspector.get_columns("flow")}
    flow_indexes = {index["name"] for index in inspector.get_indexes("flow")}

    # Suppress the SQLite foreign key warning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*SQL-parsed foreign key constraint.*")
        flow_fks = {fk["name"] for fk in inspector.get_foreign_keys("flow")}

    with op.batch_alter_table("flow", schema=None) as batch_op:
        if "flow_user_id_fkey" in flow_fks:
            batch_op.drop_constraint("flow_user_id_fkey", type_="foreignkey")
        if "ix_flow_user_id" in flow_indexes:
            batch_op.drop_index(batch_op.f("ix_flow_user_id"))
        if "user_id" in flow_columns:
            batch_op.drop_column("user_id")
        if "folder" in flow_columns:
            batch_op.drop_column("folder")
        if "updated_at" in flow_columns:
            batch_op.drop_column("updated_at")
        if "is_component" in flow_columns:
            batch_op.drop_column("is_component")