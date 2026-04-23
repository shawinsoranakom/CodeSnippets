def test_marshall_table(self):
        """Test streamlit.data_frame._marshall_table."""
        proto = Table()
        data_frame._marshall_table([[1, 2], [3, 4]], proto)
        ret = json.loads(json_format.MessageToJson(proto))
        ret = [x["int64s"]["data"] for x in ret["cols"]]
        truth = [["1", "2"], ["3", "4"]]
        self.assertEqual(ret, truth)