def migrate_add_unique_email(migrator):
    """Deduplicates user emails and add UNIQUE constraint to email column (idempotent)"""
    # step 0: check existing index state on user.email and prepare for unique constraint
    try:
        if settings.DATABASE_TYPE.upper() == "POSTGRES":
            cursor = DB.execute_sql("""
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = 'user'
                  AND indexname = 'user_email'
            """)
            result = cursor.fetchone()
            if result and result[0] > 0:
                logging.info("UNIQUE index on user.email already exists, skipping migration")
                return
        else:
            # Fetch the first index on email: tells us both the name and whether it's unique.
            # non_unique=0 means unique, non_unique=1 means non-unique.
            cursor = DB.execute_sql("""
                SELECT index_name, non_unique
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = 'user'
                  AND column_name = 'email'
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                index_name, non_unique = row
                if non_unique == 0:
                    logging.info("UNIQUE index on user.email already exists, skipping migration")
                    return
                # Non-unique index exists (e.g. from old peewee index=True); drop it so
                # the upcoming ADD UNIQUE INDEX does not hit MySQL error 1061 "Duplicate key name".
                DB.execute_sql(f"ALTER TABLE `user` DROP INDEX `{index_name}`")
                logging.info(f"Dropped non-unique index '{index_name}' on user.email before adding unique index")
    except Exception as ex:
        logging.warning(f"Failed to check/prepare email index on user table: {ex}, continuing with migration")

    # step 1: rename duplicate rows so the UNIQUE constraint can be applied
    try:
        duplicates = User.select(User.email).group_by(User.email).having(fn.COUNT(User.id) > 1).tuples()
        for (dup_email,) in duplicates:
            # Keep the superuser row, or the oldest row if there is no superuser
            rows = list(
                User
                    .select(User.id)
                    .where(User.email == dup_email)
                    .order_by(User.is_superuser.desc(), User.create_time.asc())
                    .tuples()
            )
            for (uid,) in rows[1:]:
                new_email = f"{dup_email}_DUPLICATE_{uid[:8]}"
                User.update(email=new_email).where(User.id == uid).execute()
                logging.warning("Renamed duplicate user %s email to %s during migration", uid, new_email)
    except Exception as ex:
        logging.critical("Failed to deduplicate user.email before adding UNIQUE constraint: %s", ex)
        return

    # step 2: add UNIQUE index via migrator
    try:
        migrate(migrator.add_index("user", ("email",), unique=True))
    except (OperationalError, ProgrammingError) as ex:
        msg = str(ex)
        # MySQL 1061 "Duplicate key name" or PostgreSQL "already exists" -> already migrated
        if "1061" in msg or "Duplicate key name" in msg or "already exists" in msg.lower():
            pass
        else:
            logging.critical("Failed to add UNIQUE constraint on user.email: %s", ex)
    except Exception as ex:
        logging.critical("Failed to add UNIQUE constraint on user.email: %s", ex)