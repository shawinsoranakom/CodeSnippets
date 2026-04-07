def serialize(self):
        from django.db.migrations.writer import OperationWriter

        string, imports = OperationWriter(self.value, indentation=0).serialize()
        # Nested operation, trailing comma is handled in upper
        # OperationWriter._write()
        return string.rstrip(","), imports