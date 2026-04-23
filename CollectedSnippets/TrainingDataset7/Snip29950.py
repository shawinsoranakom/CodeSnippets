def test_dumping(self):
        instance = RangesModel(
            ints=NumericRange(0, 10),
            decimals=NumericRange(empty=True),
            timestamps=DateTimeTZRange(self.lower_dt, self.upper_dt),
            timestamps_closed_bounds=DateTimeTZRange(
                self.lower_dt,
                self.upper_dt,
                bounds="()",
            ),
            dates=DateRange(self.lower_date, self.upper_date),
        )
        data = serializers.serialize("json", [instance])
        dumped = json.loads(data)
        for field in ("ints", "dates", "timestamps", "timestamps_closed_bounds"):
            dumped[0]["fields"][field] = json.loads(dumped[0]["fields"][field])
        check = json.loads(self.test_data)
        for field in ("ints", "dates", "timestamps", "timestamps_closed_bounds"):
            check[0]["fields"][field] = json.loads(check[0]["fields"][field])

        self.assertEqual(dumped, check)