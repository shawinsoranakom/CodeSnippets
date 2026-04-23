def test_restore_foreign_key_constraints_with_integrity_error(
    recorder_db_url: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test we can drop and then restore foreign keys.

    This is not supported on SQLite
    """

    constraints = (
        ("events", "data_id", "event_data", "data_id", Events),
        ("states", "old_state_id", "states", "state_id", States),
    )

    engine = create_engine(recorder_db_url)
    db_schema.Base.metadata.create_all(engine)

    # Drop constraints
    with Session(engine) as session:
        session_maker = Mock(return_value=session)
        for table, column, _, _, _ in constraints:
            migration._drop_foreign_key_constraints(
                session_maker, engine, table, column
            )

    # Add rows violating the constraints
    with Session(engine) as session:
        for _, column, _, _, table_class in constraints:
            session.add(table_class(**{column: 123}))
            session.add(table_class())
        # Insert a States row referencing the row with an invalid foreign reference
        session.add(States(old_state_id=1))
        session.commit()

    # Check we could insert the rows
    with Session(engine) as session:
        assert session.query(Events).count() == 2
        assert session.query(States).count() == 3

    # Restore constraints
    to_restore = [
        (table, column, foreign_table, foreign_column)
        for table, column, foreign_table, foreign_column, _ in constraints
    ]
    with Session(engine) as session:
        session_maker = Mock(return_value=session)
        migration._restore_foreign_key_constraints(session_maker, engine, to_restore)

    # Check the violating row has been deleted from the Events table
    with Session(engine) as session:
        assert session.query(Events).count() == 1
        assert session.query(States).count() == 3

    engine.dispose()

    assert (
        "Could not update foreign options in events table, "
        "will delete violations and try again"
    ) in caplog.text