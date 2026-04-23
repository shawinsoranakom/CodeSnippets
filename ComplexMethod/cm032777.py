async def report_status():
    """
    Periodically reports the executor's heartbeat
    """
    global PENDING_TASKS, LAG_TASKS, DONE_TASKS, FAILED_TASKS

    ip_address = await get_server_ip()
    pid = os.getpid()

    # Register the executor in Redis
    REDIS_CONN.sadd("TASKEXE", CONSUMER_NAME)
    redis_lock = RedisDistributedLock("clean_task_executor", lock_value=CONSUMER_NAME, timeout=60)

    while True:
        now = datetime.now()
        now_ts = now.timestamp()

        group_info = REDIS_CONN.queue_info(settings.get_svr_queue_name(0), SVR_CONSUMER_GROUP_NAME) or {}
        PENDING_TASKS = int(group_info.get("pending", 0))
        LAG_TASKS = int(group_info.get("lag", 0))

        current = copy.deepcopy(CURRENT_TASKS)
        heartbeat = json.dumps({
            "ip_address": ip_address,
            "pid": pid,
            "name": CONSUMER_NAME,
            "now": now.astimezone().isoformat(timespec="milliseconds"),
            "boot_at": BOOT_AT,
            "pending": PENDING_TASKS,
            "lag": LAG_TASKS,
            "done": DONE_TASKS,
            "failed": FAILED_TASKS,
            "current": current,
        })

        # Report heartbeat to Redis
        try:
            REDIS_CONN.zadd(CONSUMER_NAME, heartbeat, now_ts)
        except Exception as e:
            logging.warning(f"Failed to report heartbeat: {e}")
        else:
            logging.info(f"{CONSUMER_NAME} reported heartbeat: {heartbeat}")

        # Clean up own expired heartbeat
        try:
            REDIS_CONN.zremrangebyscore(CONSUMER_NAME, 0, now_ts - 60 * 30)
        except Exception as e:
            logging.warning(f"Failed to clean heartbeat: {e}")

        # Clean other executors
        lock_acquired = False
        try:
            lock_acquired = redis_lock.acquire()
        except Exception as e:
            logging.warning(f"Failed to acquire Redis lock: {e}")
        if lock_acquired:
            try:
                task_executors = REDIS_CONN.smembers("TASKEXE") or set()
                for worker_name in task_executors:
                    if worker_name == CONSUMER_NAME:
                        continue
                    try:
                        last_heartbeat = REDIS_CONN.REDIS.zrevrange(worker_name, 0, 0, withscores=True)
                    except Exception as e:
                        logging.warning(f"Failed to read zset for {worker_name}: {e}")
                        continue

                    if not last_heartbeat or now_ts - last_heartbeat[0][1] > WORKER_HEARTBEAT_TIMEOUT:
                        logging.info(f"{worker_name} expired, removed")
                        REDIS_CONN.srem("TASKEXE", worker_name)
                        REDIS_CONN.delete(worker_name)
            except Exception as e:
                logging.warning(f"Failed to clean other executors: {e}")
            finally:
                redis_lock.release()
        await asyncio.sleep(30)