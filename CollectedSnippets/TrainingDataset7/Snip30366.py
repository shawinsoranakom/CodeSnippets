def create_tags(self):
        self.tags = [Tag.objects.create(name=str(i)) for i in range(10)]