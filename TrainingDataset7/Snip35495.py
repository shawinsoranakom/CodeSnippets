def test_aware_datetime_in_utc(self):
        dt = datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)

        data = serializers.serialize("python", [Event(dt=dt)])
        self.assert_python_contains_datetime(data, dt)
        obj = next(serializers.deserialize("python", data)).object
        self.assertEqual(obj.dt, dt)

        data = serializers.serialize("json", [Event(dt=dt)])
        self.assert_json_contains_datetime(data, "2011-09-01T10:20:30Z")
        obj = next(serializers.deserialize("json", data)).object
        self.assertEqual(obj.dt, dt)

        data = serializers.serialize("xml", [Event(dt=dt)])
        self.assert_xml_contains_datetime(data, "2011-09-01T10:20:30+00:00")
        obj = next(serializers.deserialize("xml", data)).object
        self.assertEqual(obj.dt, dt)

        if not isinstance(
            serializers.get_serializer("yaml"), serializers.BadSerializer
        ):
            data = serializers.serialize(
                "yaml", [Event(dt=dt)], default_flow_style=None
            )
            self.assert_yaml_contains_datetime(data, "2011-09-01 10:20:30+00:00")
            obj = next(serializers.deserialize("yaml", data)).object
            self.assertEqual(obj.dt.replace(tzinfo=UTC), dt)