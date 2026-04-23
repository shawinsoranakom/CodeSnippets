def count_no_of_ways(self, task_performed):
    for i in range(len(task_performed)):
        for j in task_performed[i]:
            self.task[j].append(i)

    return self.count_ways_until(0, 1)
