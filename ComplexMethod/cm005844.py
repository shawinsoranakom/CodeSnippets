def test_upgrade_from_main_branch(db_url):
    """Verify that a DB at main's head can upgrade to current head and downgrade back.

    This catches the real-world scenario: a user running on main (or the latest release)
    upgrades to a branch with new migrations. The upgrade must succeed, the resulting
    schema must match the models, and downgrade back to main must also succeed.
    """
    from alembic.script import ScriptDirectory

    main_head = _get_main_branch_head()
    if main_head is None:
        if os.environ.get("MIGRATION_VALIDATION_CI"):
            pytest.fail("Could not determine main branch head revision — ensure fetch-depth: 0 and origin/main exists")
        pytest.skip("Could not determine main branch head revision (shallow clone or no origin/main)")

    # Check if main and branch share the same alembic head (no new migrations).
    # In that case this test is a no-op — alembic won't re-run already-applied
    # migrations, so upgrade(main_head) -> upgrade(head) does nothing.
    # Modified migrations are exercised by test_no_phantom_migrations instead.
    branch_cfg = Config()
    branch_cfg.set_main_option("script_location", str(_SCRIPT_LOCATION))
    branch_script = ScriptDirectory.from_config(branch_cfg)
    branch_heads = branch_script.get_heads()
    if len(branch_heads) == 1 and branch_heads[0] == main_head:
        pytest.skip(
            "No new migrations on this branch — main and branch share the same "
            "alembic head. Modified migrations are tested by test_no_phantom_migrations."
        )

    alembic_cfg = _make_alembic_cfg(db_url)

    # Step 1: Create DB at main's head revision (simulates existing user DB)
    command.upgrade(alembic_cfg, main_head)

    # Step 2: Upgrade to the current branch head
    command.upgrade(alembic_cfg, "head")

    # Step 3: Verify models match the migrated DB
    engine = create_engine(_engine_url(db_url))
    try:
        with engine.connect() as connection:
            migration_context = MigrationContext.configure(connection)
            diffs = compare_metadata(migration_context, SQLModel.metadata)
    finally:
        engine.dispose()

    significant_diffs = _filter_diffs(diffs, db_url)

    if significant_diffs:
        diff_descriptions = "\n".join(str(d) for d in significant_diffs)
        pytest.fail(
            f"After upgrading from main ({main_head}) to head, "
            f"autogenerate detected {len(significant_diffs)} schema mismatch(es).\n\n"
            f"Diffs:\n{diff_descriptions}"
        )

    # Step 4: Downgrade back to main's head to verify rollback works
    command.downgrade(alembic_cfg, main_head)

    # Step 5: Verify the DB is actually at main's revision after downgrade
    engine = create_engine(_engine_url(db_url))
    try:
        with engine.connect() as connection:
            ctx = MigrationContext.configure(connection)
            current_rev = ctx.get_current_revision()
            assert current_rev == main_head, f"After downgrade, expected revision {main_head} but got {current_rev}"
    finally:
        engine.dispose()