def get_queryset(self):
        return Book.does_not_exist.all()