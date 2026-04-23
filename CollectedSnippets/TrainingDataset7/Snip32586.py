def items(self):
        return Entry.objects.exclude(title="My last entry")