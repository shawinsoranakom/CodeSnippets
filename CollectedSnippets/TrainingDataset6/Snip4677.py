async def test_async_gen():
        cm = asynccontextmanager(get_db)
        async with cm() as db_session:
            return db_session