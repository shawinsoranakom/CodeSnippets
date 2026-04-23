def push(self, item: int) -> None:
    self.temp_queue.append(item)
    while self.main_queue:
        self.temp_queue.append(self.main_queue.popleft())
    self.main_queue, self.temp_queue = self.temp_queue, self.main_queue
