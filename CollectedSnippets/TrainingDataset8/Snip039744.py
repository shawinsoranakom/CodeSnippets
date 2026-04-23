def test_create_page_profile_message(self):
        """Test creating the page profile message via create_page_profile_message."""
        forward_msg = metrics_util.create_page_profile_message(
            commands=[
                metrics_util._get_command_telemetry(
                    st.dataframe, "dataframe", pd.DataFrame(), width=250
                )
            ],
            exec_time=1000,
            prep_time=2000,
        )

        self.assertEqual(len(forward_msg.page_profile.commands), 1)
        self.assertEqual(forward_msg.page_profile.exec_time, 1000)
        self.assertEqual(forward_msg.page_profile.prep_time, 2000)
        self.assertEqual(forward_msg.page_profile.commands[0].name, "dataframe")