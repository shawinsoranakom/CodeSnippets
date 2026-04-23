def get_resultclass(self):
        if self.debug_sql:
            return DebugSQLTextTestResult
        elif self.pdb:
            return PDBDebugResult