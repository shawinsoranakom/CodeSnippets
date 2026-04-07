def get(self, request):
        self.object_list = self.get_queryset()