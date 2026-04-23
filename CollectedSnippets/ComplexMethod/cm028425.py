def __init__(self,
               tasks: Union[Dict[Text, base_task.Task], List[base_task.Task]],
               task_weights: Optional[Dict[str, Union[float, int]]] = None,
               task_eval_steps: Optional[Dict[str, int]] = None,
               name: Optional[str] = None):
    """MultiTask initialization.

    Args:
      tasks: a list or a flat dict of Task.
      task_weights: a dict of (task, task weight), task weight can be applied
        directly during loss summation in a joint backward step, or it can be
        used to sample task among interleaved backward step.
      task_eval_steps: a dict of (task, eval steps).
      name: the instance name of a MultiTask object.
    """
    super().__init__(name=name)
    if isinstance(tasks, list):
      self._tasks = {}
      for task in tasks:
        if task.name in self._tasks:
          raise ValueError("Duplicated tasks found, task.name is %s" %
                           task.name)
        self._tasks[task.name] = task
    elif isinstance(tasks, dict):
      self._tasks = tasks
    else:
      raise ValueError("The tasks argument has an invalid type: %s" %
                       type(tasks))
    self.task_eval_steps = task_eval_steps or {}
    self._task_weights = task_weights or {}
    self._task_weights = dict([
        (name, self._task_weights.get(name, 1.0)) for name in self.tasks
    ])