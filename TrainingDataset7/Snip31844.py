def test_check_model_instance_from_subview(self):
        url = "/check_model_instance_from_subview/?%s" % urlencode(
            {
                "url": self.live_server_url,
            }
        )
        with self.urlopen(url) as f:
            self.assertIn(b"emily", f.read())