def test_if_check_duplicate_links_has_the_correct_return(self):
        result_1 = check_duplicate_links(self.duplicate_links)
        result_2 = check_duplicate_links(self.no_duplicate_links)

        self.assertIsInstance(result_1, tuple)
        self.assertIsInstance(result_2, tuple)

        has_duplicate_links, links = result_1
        no_duplicate_links, no_links = result_2

        self.assertTrue(has_duplicate_links)
        self.assertFalse(no_duplicate_links)

        self.assertIsInstance(links, list)
        self.assertIsInstance(no_links, list)

        self.assertEqual(len(links), 2)
        self.assertEqual(len(no_links), 0)

    def test_if_fake_user_agent_has_a_str_as_return(self):
        user_agent = fake_user_agent()
        self.assertIsInstance(user_agent, str)

    def test_get_host_from_link(self):
        links = [
            'example.com',
            'https://example.com',
            'https://www.example.com',
            'https://www.example.com.br',
            'https://www.example.com/route',
            'https://www.example.com?p=1&q=2',
            'https://www.example.com#anchor'
        ]

        for link in links:
            host = get_host_from_link(link)

            with self.subTest():
                self.assertIsInstance(host, str)

                self.assertNotIn('://', host)
                self.assertNotIn('/', host)
                self.assertNotIn('?', host)
                self.assertNotIn('#', host)

        with self.assertRaises(TypeError):
            get_host_from_link()
