def __init__(self, alias, params):
        self.alias = alias
        self.queues = set(params.get("QUEUES", [DEFAULT_TASK_QUEUE_NAME]))
        self.options = params.get("OPTIONS", {})