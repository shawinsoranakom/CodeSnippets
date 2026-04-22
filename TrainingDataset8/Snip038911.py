def test_marshall_any_array(self):
        """Test streamlit.data_frame._marshall_any_array."""
        # list
        list_data = [1, 2]
        list_proto = AnyArray()

        data_frame._marshall_any_array(list_data, list_proto)
        self.assertEqual(list_proto.int64s.data, list_data)

        # wrong shape
        with pytest.raises(ValueError) as e:
            data_frame._marshall_any_array([[1, 2], [3, 4]], AnyArray())
        err_msg = "Array must be 1D."
        self.assertEqual(err_msg, str(e.value))

        # float
        float_data = pd.Series(np.array([1.0, 2.0]), dtype=np.floating)
        float_proto = AnyArray()

        data_frame._marshall_any_array(float_data, float_proto)
        self.assertEqual(float_proto.doubles.data, float_data.tolist())

        # timedelta64
        td_data = np.array([1, 2], dtype=np.timedelta64)
        td_proto = AnyArray()

        data_frame._marshall_any_array(td_data, td_proto)
        self.assertEqual(td_proto.timedeltas.data, td_data.tolist())

        # int
        int_data = np.array([1, 2], dtype=np.integer)
        int_proto = AnyArray()

        data_frame._marshall_any_array(int_data, int_proto)
        self.assertEqual(int_proto.int64s.data, int_data.tolist())

        # bool
        bool_data = np.array([True, False], dtype=np.bool)
        bool_proto = AnyArray()

        data_frame._marshall_any_array(bool_data, bool_proto)
        self.assertEqual(bool_proto.int64s.data, bool_data.tolist())

        # object
        obj_data = np.array([json.dumps, json.dumps], dtype=np.object)
        obj_proto = AnyArray()
        truth = [str(json.dumps), str(json.dumps)]

        data_frame._marshall_any_array(obj_data, obj_proto)
        self.assertEqual(obj_proto.strings.data, truth)

        # StringDtype
        string_data = pd.Series(["foo", "bar", "baz"], dtype="string")
        string_proto = AnyArray()
        data_frame._marshall_any_array(string_data, string_proto)
        self.assertEqual(string_proto.strings.data, string_data.tolist())

        # No timezone
        dt_data = pd.Series([np.datetime64("2019-04-09T12:34:56")])
        dt_proto = AnyArray()

        obj_to_patch = "streamlit.elements.legacy_data_frame.tzlocal.get_localzone"
        with patch(obj_to_patch) as p:
            p.return_value = "America/Los_Angeles"
            data_frame._marshall_any_array(dt_data, dt_proto)
            self.assertEqual("2019-04-09T12:34:56", dt_proto.datetimes.data[0])

        # With timezone
        dt_data = pd.Series([np.datetime64("2019-04-09T12:34:56")])
        dt_data = dt_data.dt.tz_localize("UTC")
        dt_proto = AnyArray()
        data_frame._marshall_any_array(dt_data, dt_proto)
        self.assertEqual("2019-04-09T12:34:56+00:00", dt_proto.datetimes.data[0])

        # string
        str_data = np.array(["random", "string"])
        str_proto = AnyArray()

        with pytest.raises(NotImplementedError, match="^Dtype <U6 not understood.$"):
            data_frame._marshall_any_array(str_data, str_proto)