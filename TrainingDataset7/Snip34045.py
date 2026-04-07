def test_repr(self):
        url_node = URLNode(view_name="named-view", args=[], kwargs={}, asvar=None)
        self.assertEqual(
            repr(url_node),
            "<URLNode view_name='named-view' args=[] kwargs={} as=None>",
        )
        url_node = URLNode(
            view_name="named-view",
            args=[1, 2],
            kwargs={"action": "update"},
            asvar="my_url",
        )
        self.assertEqual(
            repr(url_node),
            "<URLNode view_name='named-view' args=[1, 2] "
            "kwargs={'action': 'update'} as='my_url'>",
        )