def test_check_cached_value_pk_different_type(self):
        """Primary key is not checked if the content type doesn't match."""
        board = Board.objects.create(name="some test")
        oddrel = OddRelation1.objects.create(name="clink")
        charlink = CharLink.objects.create(content_object=oddrel)
        charlink = CharLink.objects.get(pk=charlink.pk)
        self.assertEqual(charlink.content_object, oddrel)
        charlink.object_id = board.pk
        charlink.content_type_id = ContentType.objects.get_for_model(Board).id
        self.assertEqual(charlink.content_object, board)