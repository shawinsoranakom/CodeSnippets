def __init__(self, alias, params):
        super().__init__(alias, params)
        self.worker_id = get_random_string(32)