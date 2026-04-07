def __init__(self, database_operations=None, state_operations=None):
        self.database_operations = database_operations or []
        self.state_operations = state_operations or []