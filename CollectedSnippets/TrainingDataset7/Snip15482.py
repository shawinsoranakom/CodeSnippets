def save(self, *args, **kwargs):
        while not self.rand_pk:
            test_pk = random.randint(1, 99999)
            if not NonAutoPKBook.objects.filter(rand_pk=test_pk).exists():
                self.rand_pk = test_pk
        super().save(*args, **kwargs)