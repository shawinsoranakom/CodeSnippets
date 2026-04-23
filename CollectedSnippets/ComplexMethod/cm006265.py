def upgrade() -> None:
    conn = op.get_bind()
    # Check which columns already exist (handles fresh DB where model creates them)
    inspector = sa.inspect(conn)
    existing_columns = {col["name"] for col in inspector.get_columns("job")}
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("job")}
    job_type_enum = sa.Enum("workflow", "ingestion", "evaluation", name="job_type_enum")
    job_type_enum.create(conn, checkfirst=True)

    with op.batch_alter_table("job", schema=None) as batch_op:
        if "type" not in existing_columns:
            batch_op.add_column(sa.Column("type", job_type_enum, nullable=True))
        if "user_id" not in existing_columns:
            batch_op.add_column(sa.Column("user_id", sa.Uuid(), nullable=True))
        if "ix_job_status" in existing_indexes:
            batch_op.drop_index(batch_op.f("ix_job_status"))
        if "ix_job_type" not in existing_indexes:
            batch_op.create_index(batch_op.f("ix_job_type"), ["type"], unique=False)
        if "ix_job_user_id" not in existing_indexes:
            batch_op.create_index(batch_op.f("ix_job_user_id"), ["user_id"], unique=False)