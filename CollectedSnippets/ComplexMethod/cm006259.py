def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    try:
        # Re-create the dropped table 'flowstyle' if it was previously dropped in upgrade
        if "flowstyle" not in inspector.get_table_names():
            op.create_table(
                "flowstyle",
                sa.Column("color", sa.String(), nullable=False),
                sa.Column("emoji", sa.String(), nullable=False),
                sa.Column("flow_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=True),
                sa.Column("id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
                sa.ForeignKeyConstraint(["flow_id"], ["flow.id"]),
                sa.PrimaryKeyConstraint("id"),
                sa.UniqueConstraint("id"),
            )

        with op.batch_alter_table("flow", schema=None) as batch_op:
            # Check and remove newly added columns and constraints in upgrade
            flow_columns = [column["name"] for column in inspector.get_columns("flow")]
            if "user_id" in flow_columns:
                batch_op.drop_column("user_id")
            if "folder" in flow_columns:
                batch_op.drop_column("folder")
            if "updated_at" in flow_columns:
                batch_op.drop_column("updated_at")
            if "is_component" in flow_columns:
                batch_op.drop_column("is_component")

            indices = inspector.get_indexes("flow")
            indices_names = [index["name"] for index in indices]
            if "ix_flow_user_id" in indices_names:
                batch_op.drop_index("ix_flow_user_id")
            # Assuming fk_flow_user_id_user is a foreign key constraint's name, not an index
            constraints = inspector.get_foreign_keys("flow")
            constraint_names = [constraint["name"] for constraint in constraints]
            if "fk_flow_user_id_user" in constraint_names:
                batch_op.drop_constraint("fk_flow_user_id_user", type_="foreignkey")

    except Exception as e:  # noqa: BLE001
        # It's generally a good idea to log the exception or handle it in a way other than a bare pass
        logger.exception(f"Error during downgrade: {e}")