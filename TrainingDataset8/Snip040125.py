def test_dirty_data_dict_is_not_plotly_chart(self):
        trace0 = go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17])
        trace1 = go.Scatter(x=[1, 2, 3, 4], y=[16, 5, 11, 9])
        d = {"data": [trace0, trace1], "foo": "bar"}  # Illegal property!

        res = type_util.is_plotly_chart(d)
        self.assertFalse(res)