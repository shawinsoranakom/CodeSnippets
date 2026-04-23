def test_serialize_superfluous_queries(self):
        """Ensure no superfluous queries are made when serializing ForeignKeys

        #17602
        """
        ac = Actor(name="Actor name")
        ac.save()
        mv = Movie(title="Movie title", actor_id=ac.pk)
        mv.save()

        with self.assertNumQueries(0):
            serializers.serialize(self.serializer_name, [mv])