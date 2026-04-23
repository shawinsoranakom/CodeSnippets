def test_aware_datetime_in_local_timezone(self):
        dt = datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT)

        data = serializers.serialize("python", [Event(dt=dt)])
        self.assert_python_contains_datetime(data, dt)
        obj = next(serializers.deserialize("python", data)).object
        self.assertEqual(obj.dt, dt)

        data = serializers.serialize("json", [Event(dt=dt)])
        self.assert_json_contains_datetime(data, "2011-09-01T13:20:30+03:00")
        obj = next(serializers.deserialize("json", data)).object
        self.assertEqual(obj.dt, dt)

        data = serializers.serialize("xml", [Event(dt=dt)])
        self.assert_xml_contains_datetime(data, "2011-09-01T13:20:30+03:00")
        obj = next(serializers.deserialize("xml", data)).object
        self.assertEqual(obj.dt, dt)

        if not isinstance(
            serializers.get_serializer("yaml"), serializers.BadSerializer
        ):
            data = serializers.serialize(
                "yaml", [Event(dt=dt)], default_flow_style=None
            )
            self.assert_yaml_contains_datetime(data, "2011-09-01 13:20:30+03:00")
            obj = next(serializers.deserialize("yaml", data)).object
            if HAS_YAML and yaml.__version__ < "5.3":
                self.assertEqual(obj.dt.replace(tzinfo=UTC), dt)
            else:
                self.assertEqual(obj.dt, dt)