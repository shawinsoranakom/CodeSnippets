def test_expand_phase_compatibility_and_rollback(self):
        """Simulate an EXPAND phase migration and verify N-1 compatibility and rollback."""
        # 1. Setup Initial State (Version N-1)
        engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        # Initial Schema
        users = Table(
            "users", metadata, Column("id", Integer, primary_key=True), Column("username", String, nullable=False)
        )
        metadata.create_all(engine)

        # Populate with some data using "Old Service"
        with engine.connect() as conn:
            conn.execute(users.insert().values(username="user_v1"))
            conn.commit()

        # 2. Apply EXPAND Migration (Version N)
        # Guideline: Add new column as nullable
        with engine.connect() as conn:
            # Verify idempotency check logic works (simulated)
            inspector = sa.inspect(conn)
            if "email" not in [c["name"] for c in inspector.get_columns("users")]:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR NULL"))
                conn.commit()

        # 3. Verify N-1 Compatibility
        with engine.connect() as conn:
            # Can "Old Service" still read?
            # (Select * might get extra column, but mapped ORM usually ignores unknown unless strict)
            # Raw SQL insert from old service (doesn't know about email)
            try:
                conn.execute(text("INSERT INTO users (username) VALUES ('user_v1_after_migration')"))
                conn.commit()
            except Exception as e:
                pytest.fail(f"Old service broke after migration: {e}")

            # Can "New Service" use new features?
            conn.execute(text("INSERT INTO users (username, email) VALUES ('user_v2', 'test@example.com')"))
            conn.commit()

        # 4. Verify Rollback Safety
        # Guideline: Check for data in new column before dropping
        with engine.connect() as conn:
            # Check for data
            count = conn.execute(text("SELECT COUNT(*) FROM users WHERE email IS NOT NULL")).scalar()
            assert count is not None, "Count should not be None"
            assert count > 0, "Should have data in new column"

            # In a real scenario, we would backup here if count > 0
            # For this test, we proceed to drop, simulating the downgrade() op

            # SQLite support for DROP COLUMN
            conn.execute(text("ALTER TABLE users DROP COLUMN email"))
            conn.commit()

        # 5. Verify Post-Rollback State
        with engine.connect() as conn:
            inspector = sa.inspect(conn)
            columns = [c["name"] for c in inspector.get_columns("users")]
            assert "email" not in columns
            assert "username" in columns

            # Verify data integrity of original columns
            rows = conn.execute(text("SELECT username FROM users")).fetchall()
            usernames = [r[0] for r in rows]
            assert "user_v1" in usernames
            assert "user_v1_after_migration" in usernames
            assert "user_v2" in usernames