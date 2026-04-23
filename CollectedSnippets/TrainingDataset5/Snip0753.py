def count_ways_until(self, mask, task_no):
    if mask == self.final_mask:
        return 1

    if task_no > self.total_tasks:
        return 0

    if self.dp[mask][task_no] != -1:
        return self.dp[mask][task_no]

    total_ways_until = self.count_ways_until(mask, task_no + 1)

    if task_no in self.task:
        for p in self.task[task_no]:
            if mask & (1 << p):
                continue

            total_ways_until += self.count_ways_until(mask | (1 << p), task_no + 1)

    self.dp[mask][task_no] = total_ways_until

    return self.dp[mask][task_no]
