def __init__(self, migration, include_header=True):
        self.migration = migration
        self.include_header = include_header
        self.needs_manual_porting = False