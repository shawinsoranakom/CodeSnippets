def patched_has_table(migration_recorder):
            if migration_recorder.connection is connections["other"]:
                raise Exception("Other connection")
            else:
                return mock.DEFAULT