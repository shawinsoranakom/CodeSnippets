def __call__(self, *args, **kwargs):
        session_id = args[0] if args else kwargs.get("session_id")
        if not session_id:
            return super().__call__(*args, **kwargs)

        lock_key = f"lock:{session_id}"
        lock_info = redis_client.get(f"lock_info:{session_id}")
        if lock_info:
            try:
                lock_data = json.loads(lock_info.decode("utf-8"))
                lock_time = lock_data.get("timestamp", 0)
                if time.time() - lock_time > STALE_LOCK_THRESHOLD_SEC:
                    redis_client.delete(lock_key)
                    redis_client.delete(f"lock_info:{session_id}")
            except (ValueError, TypeError) as e:
                print(f"Error checking lock time: {e}")

        acquired = redis_client.set(lock_key, "1", nx=True, ex=REDIS_LOCK_EXP_TIME_SEC)
        if acquired:
            lock_data = {"timestamp": time.time(), "task_id": self.request.id if hasattr(self, "request") else None}
            redis_client.set(f"lock_info:{session_id}", json.dumps(lock_data), ex=REDIS_LOCK_INFO_EXP_TIME_SEC)

        if not acquired:
            return {
                "error": "Session busy",
                "response": "This session is already processing a message. Please wait.",
                "session_id": session_id,
                "stage": "busy",
                "session_state": "{}",
                "is_processing": True,
                "process_type": "chat",
            }

        try:
            return super().__call__(*args, **kwargs)
        finally:
            redis_client.delete(lock_key)
            redis_client.delete(f"lock_info:{session_id}")