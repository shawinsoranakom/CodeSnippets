def test_ticket6074(self):
        # Merging two empty result sets shouldn't leave a queryset with no
        # constraints (which would match everything).
        self.assertSequenceEqual(Author.objects.filter(Q(id__in=[])), [])
        self.assertSequenceEqual(Author.objects.filter(Q(id__in=[]) | Q(id__in=[])), [])