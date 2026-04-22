def test_machine_id_v3_from_etc(self):
        """Test getting the machine id from /etc"""
        file_data = "etc"

        with patch(
            "streamlit.runtime.metrics_util.uuid.getnode", return_value=MAC
        ), patch(
            "streamlit.runtime.metrics_util.open",
            mock_open(read_data=file_data),
            create=True,
        ), patch(
            "streamlit.runtime.metrics_util.os.path.isfile",
            side_effect=lambda path: path == "/etc/machine-id",
        ):
            machine_id = metrics_util._get_machine_id_v3()
        self.assertEqual(machine_id, file_data)