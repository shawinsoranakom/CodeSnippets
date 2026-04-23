def test_drop_duplicated_foreign_key_constraints(recorder_db_url: str) -> None:
    """Test we can drop and then restore foreign keys.

    This is not supported on SQLite
    """

    constraints_to_recreate = (
        ("events", "data_id", "event_data", "data_id"),
        ("states", "event_id", None, None),  # This won't be found
        ("states", "old_state_id", "states", "state_id"),
    )

    db_engine = recorder_db_url.partition("://")[0]

    expected_dropped_constraints = {
        "mysql": [
            (
                "events",
                "data_id",
                {
                    "constrained_columns": ["data_id"],
                    "name": ANY,
                    "options": {},
                    "referred_columns": ["data_id"],
                    "referred_schema": None,
                    "referred_table": "event_data",
                },
            ),
            (
                "states",
                "old_state_id",
                {
                    "constrained_columns": ["old_state_id"],
                    "name": ANY,
                    "options": {},
                    "referred_columns": ["state_id"],
                    "referred_schema": None,
                    "referred_table": "states",
                },
            ),
        ],
        "postgresql": [
            (
                "events",
                "data_id",
                {
                    "comment": None,
                    "constrained_columns": ["data_id"],
                    "name": ANY,
                    "options": {},
                    "referred_columns": ["data_id"],
                    "referred_schema": None,
                    "referred_table": "event_data",
                },
            ),
            (
                "states",
                "old_state_id",
                {
                    "comment": None,
                    "constrained_columns": ["old_state_id"],
                    "name": ANY,
                    "options": {},
                    "referred_columns": ["state_id"],
                    "referred_schema": None,
                    "referred_table": "states",
                },
            ),
        ],
    }

    def find_constraints(
        engine: Engine, table: str, column: str
    ) -> list[tuple[str, str, ReflectedForeignKeyConstraint]]:
        inspector = inspect(engine)
        return [
            (table, column, foreign_key)
            for foreign_key in inspector.get_foreign_keys(table)
            if foreign_key["name"] and foreign_key["constrained_columns"] == [column]
        ]

    engine = create_engine(recorder_db_url)
    db_schema.Base.metadata.create_all(engine)

    # Create a duplicate of the constraints
    inspector = Mock(name="inspector")
    inspector.get_foreign_keys = Mock(name="get_foreign_keys", return_value=[])
    with (
        patch(
            "homeassistant.components.recorder.migration.sqlalchemy.inspect",
            return_value=inspector,
        ),
        Session(engine) as session,
    ):
        session_maker = Mock(return_value=session)
        migration._restore_foreign_key_constraints(
            session_maker, engine, constraints_to_recreate
        )

    matching_constraints_1 = [
        dropped_constraint
        for table, column, _, _ in constraints_to_recreate
        for dropped_constraint in find_constraints(engine, table, column)
    ]
    _expected_dropped_constraints = [
        _dropped_constraint
        for dropped_constraint in expected_dropped_constraints[db_engine]
        for _dropped_constraint in (dropped_constraint, dropped_constraint)
    ]
    assert matching_constraints_1 == _expected_dropped_constraints

    with Session(engine) as session:
        session_maker = Mock(return_value=session)
        for table, column, _, _ in constraints_to_recreate:
            migration._drop_foreign_key_constraints(
                session_maker, engine, table, column
            )

    # Check we don't find the constrained columns again (they are removed)
    matching_constraints_2 = [
        dropped_constraint
        for table, column, _, _ in constraints_to_recreate
        for dropped_constraint in find_constraints(engine, table, column)
    ]
    assert matching_constraints_2 == []

    # Restore the constraints
    with Session(engine) as session:
        session_maker = Mock(return_value=session)
        migration._restore_foreign_key_constraints(
            session_maker, engine, constraints_to_recreate
        )

    # Check we do find a single the constrained columns again (they are restored
    # only once, even though we called _restore_foreign_key_constraints twice)
    matching_constraints_3 = [
        dropped_constraint
        for table, column, _, _ in constraints_to_recreate
        for dropped_constraint in find_constraints(engine, table, column)
    ]
    assert matching_constraints_3 == expected_dropped_constraints[db_engine]

    engine.dispose()