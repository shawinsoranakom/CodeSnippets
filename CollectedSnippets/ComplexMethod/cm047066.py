def get_all_tasks(self, page: int, page_size: int):
        start = (page - 1) * page_size
        end = start + page_size
        tasks = []
        cursor = 0
        total = 0
        while True:
            cursor, keys = self._redis.scan(cursor, count=page_size)
            total += len(keys)
            if total > start:
                for key in keys[max(0, start - total):end - total]:
                    task_data = self._redis.hgetall(key)
                    task = {
                        k.decode("utf-8"): self._convert_to_original_type(v) for k, v in task_data.items()
                    }
                    tasks.append(task)
                    if len(tasks) >= page_size:
                        break
            if cursor == 0 or len(tasks) >= page_size:
                break
        return tasks, total