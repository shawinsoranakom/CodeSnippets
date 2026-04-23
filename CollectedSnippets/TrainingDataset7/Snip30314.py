def test_proxy_load_from_fixture(self):
        management.call_command("loaddata", "mypeople.json", verbosity=0)
        p = MyPerson.objects.get(pk=100)
        self.assertEqual(p.name, "Elvis Presley")