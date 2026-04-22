def test_machine_id_v3_from_node(self):
        """Test getting the machine id as the mac address"""

        with patch(
            "streamlit.runtime.metrics_util.uuid.getnode", return_value=MAC
        ), patch("streamlit.runtime.metrics_util.os.path.isfile", return_value=False):

            machine_id = metrics_util._get_machine_id_v3()
        self.assertEqual(machine_id, MAC)