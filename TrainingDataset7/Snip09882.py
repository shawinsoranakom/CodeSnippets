def getquoted(self):
            quoted = super().getquoted()
            return quoted + b"::jsonb"