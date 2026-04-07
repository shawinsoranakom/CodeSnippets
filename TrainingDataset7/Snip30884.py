def test_ticket_21203(self):
        p = Ticket21203Parent.objects.create(parent_bool=True)
        c = Ticket21203Child.objects.create(parent=p)
        qs = Ticket21203Child.objects.select_related("parent").defer("parent__created")
        self.assertSequenceEqual(qs, [c])
        self.assertIs(qs[0].parent.parent_bool, True)