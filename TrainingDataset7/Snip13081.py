def _store_result(self, result):
        object.__setattr__(result, "enqueued_at", timezone.now())
        self.results.append(result)
        task_enqueued.send(type(self), task_result=result)