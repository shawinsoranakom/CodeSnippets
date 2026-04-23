def _clean_up_subscriber(self, subscriber_id: str, callback_id: str) -> None:
        if subscriber_id not in self._subscribers:
            logger.warning(f'Subscriber not found during cleanup: {subscriber_id}')
            return
        if callback_id not in self._subscribers[subscriber_id]:
            logger.warning(f'Callback not found during cleanup: {callback_id}')
            return
        if (
            subscriber_id in self._thread_loops
            and callback_id in self._thread_loops[subscriber_id]
        ):
            loop = self._thread_loops[subscriber_id][callback_id]
            current_task = asyncio.current_task(loop)
            pending = [
                task for task in asyncio.all_tasks(loop) if task is not current_task
            ]
            for task in pending:
                task.cancel()
            try:
                loop.stop()
                loop.close()
            except Exception as e:
                logger.warning(
                    f'Error closing loop for {subscriber_id}/{callback_id}: {e}'
                )
            del self._thread_loops[subscriber_id][callback_id]

        if (
            subscriber_id in self._thread_pools
            and callback_id in self._thread_pools[subscriber_id]
        ):
            pool = self._thread_pools[subscriber_id][callback_id]
            pool.shutdown()
            del self._thread_pools[subscriber_id][callback_id]

        del self._subscribers[subscriber_id][callback_id]