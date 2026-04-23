async def benchmark_once(
    n_keys: int,
    iterations: int = 100,
    async_db_session: AsyncSession | None = None,
):
    settings_service = None
    try:
        settings_service = get_settings_service()
    except Exception:
        settings_service = None

    stored_rows = []
    # generate N keys, keep one matching candidate_key to test hit
    candidate_raw = f"sk-test-{uuid.uuid4()}"

    for i in range(n_keys):
        raw = f"sk-test-{uuid.uuid4()}"
        if i == n_keys - 1:
            raw = candidate_raw
        try:
            stored = auth_utils.encrypt_api_key(raw, settings_service=settings_service)
        except Exception:
            stored = f"enc-{raw}"
        stored_rows.append((str(i), stored, str(uuid.uuid4())))

    if async_db_session is not None:
        # use provided async session fixture to mimic DB
        db_session = async_db_session
        # create a user
        user = User(username=f"u-{uuid.uuid4()}", password=_get_test_password())
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        for i, (_, stored, _uid) in enumerate(stored_rows):
            api = ApiKey(api_key=stored, name=f"k-{i}", user_id=user.id)
            db_session.add(api)
        await db_session.commit()

        timings = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            await api_key_crud._check_key_from_db(db_session, candidate_raw, settings_service)
            t1 = time.perf_counter()
            timings.append((t1 - t0) * 1000.0)  # ms

    mean = statistics.mean(timings)
    p50 = statistics.median(timings)
    total_ms = sum(timings)
    return {
        "n_keys": n_keys,
        "iterations": iterations,
        "mean_ms": mean,
        "p50_ms": p50,
        "total_ms": total_ms,
    }