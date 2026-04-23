def get_object(self, request, entry_id):
        return Entry.objects.get(pk=entry_id)