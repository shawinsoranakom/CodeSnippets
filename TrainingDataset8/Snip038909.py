def test_marshall_index(self):
        """Test streamlit.data_frame._marshall_index."""
        df = pd.DataFrame(data={"col1": [1, 2], "col2": [3, 4]})

        # Plain Index
        proto = Index()
        data_frame._marshall_index(df.columns, proto)
        self.assertEqual(["col1", "col2"], proto.plain_index.data.strings.data)

        # Range Index
        proto = Index()
        data_frame._marshall_index(df.index, proto)
        self.assertEqual(0, proto.range_index.start)
        self.assertEqual(2, proto.range_index.stop)

        # Range Index with NaNs
        df_nan = pd.DataFrame(data={"col1": [], "col2": []})
        proto = Index()
        data_frame._marshall_index(df_nan.index, proto)
        self.assertEqual(0, proto.range_index.start)
        self.assertEqual(0, proto.range_index.stop)

        # multi index
        df_multi = pd.MultiIndex.from_arrays([[1, 2], [3, 4]], names=["one", "two"])
        proto = Index()
        data_frame._marshall_index(df_multi, proto)
        self.assertEqual([1, 2], proto.multi_index.levels[0].int_64_index.data.data)
        self.assertEqual([0, 1], proto.multi_index.labels[0].data)

        # datetimeindex
        truth = [
            "2019-04-01T10:00:00-07:00",
            "2019-04-01T11:00:00-07:00",
            "2019-04-01T12:00:00-07:00",
        ]
        df_dt = pd.date_range(
            start="2019/04/01 10:00", end="2019/04/01 12:00", freq="H"
        )
        proto = Index()
        obj_to_patch = "streamlit.elements.legacy_data_frame.tzlocal.get_localzone"
        with patch(obj_to_patch) as p:
            p.return_value = "America/Los_Angeles"
            data_frame._marshall_index(df_dt, proto)
            self.assertEqual(truth, proto.datetime_index.data.data)

        # timedeltaindex
        df_td = pd.to_timedelta(np.arange(1, 5), unit="ns")
        proto = Index()
        data_frame._marshall_index(df_td, proto)
        self.assertEqual([1, 2, 3, 4], proto.timedelta_index.data.data)

        # int64index
        df_int64 = pd.Int64Index(np.arange(1, 5))
        proto = Index()
        data_frame._marshall_index(df_int64, proto)
        self.assertEqual([1, 2, 3, 4], proto.int_64_index.data.data)

        # float64index
        df_float64 = pd.Float64Index(np.arange(1, 5))
        proto = Index()
        data_frame._marshall_index(df_float64, proto)
        self.assertEqual([1, 2, 3, 4], proto.float_64_index.data.data)

        # Period index
        df_period = pd.period_range(
            start="2005-12-21 08:45", end="2005-12-21 11:55", freq="H"
        )
        proto = Index()
        with pytest.raises(NotImplementedError) as e:
            data_frame._marshall_index(df_period, proto)
        err_msg = (
            "Can't handle <class 'pandas.core.indexes.period.PeriodIndex'>" " yet."
        )
        self.assertEqual(err_msg, str(e.value))