def test_get_external_ip(self):
        # Test success
        with requests_mock.mock() as m:
            m.get(net_util._AWS_CHECK_IP, text="1.2.3.4")
            self.assertEqual("1.2.3.4", net_util.get_external_ip())

        net_util._external_ip = None

        # Test failure
        with requests_mock.mock() as m:
            m.get(net_util._AWS_CHECK_IP, exc=requests.exceptions.ConnectTimeout)
            self.assertEqual(None, net_util.get_external_ip())