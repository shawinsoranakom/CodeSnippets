def _try_with_lock(lock_name: str, process_func, check_func, timeout: int = None):
    """Execute function with distributed lock."""
    if not timeout:
        timeout = int(os.environ.get("OB_DDL_TIMEOUT", "60"))

    if not check_func():
        from rag.utils.redis_conn import RedisDistributedLock
        lock = RedisDistributedLock(lock_name)
        if lock.acquire():
            try:
                process_func()
                return
            except Exception as e:
                if "Duplicate" in str(e):
                    return
                raise
            finally:
                lock.release()

    if not check_func():
        time.sleep(1)
        count = 1
        while count < timeout and not check_func():
            count += 1
            time.sleep(1)
        if count >= timeout and not check_func():
            raise Exception(f"Timeout to wait for process complete for {lock_name}.")