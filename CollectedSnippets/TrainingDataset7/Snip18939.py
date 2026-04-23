def test_concurrent_delete_with_save(self):
        """
        Test fetching, deleting and finally saving an object - we should get
        an insert in this case.
        """
        a = Article.objects.create(headline="foo", pub_date=datetime.now())
        exceptions = []

        def deleter():
            try:
                # Do not delete a directly - doing so alters its state.
                Article.objects.filter(pk=a.pk).delete()
            except Exception as e:
                exceptions.append(e)
            finally:
                connections[DEFAULT_DB_ALIAS].close()

        self.assertEqual(len(exceptions), 0)
        t = threading.Thread(target=deleter)
        t.start()
        t.join()
        a.save()
        self.assertEqual(Article.objects.get(pk=a.pk).headline, "foo")