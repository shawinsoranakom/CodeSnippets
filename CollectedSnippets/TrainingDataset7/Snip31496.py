def test_add_datefield_and_datetimefield_use_effective_default(
        self, mocked_datetime, mocked_tz
    ):
        """
        effective_default() should be used for DateField, DateTimeField, and
        TimeField if auto_now or auto_now_add is set (#25005).
        """
        now = datetime.datetime(month=1, day=1, year=2000, hour=1, minute=1)
        now_tz = datetime.datetime(
            month=1, day=1, year=2000, hour=1, minute=1, tzinfo=datetime.UTC
        )
        mocked_datetime.now = mock.MagicMock(return_value=now)
        mocked_tz.now = mock.MagicMock(return_value=now_tz)
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Check auto_now/auto_now_add attributes are not defined
        columns = self.column_classes(Author)
        self.assertNotIn("dob_auto_now", columns)
        self.assertNotIn("dob_auto_now_add", columns)
        self.assertNotIn("dtob_auto_now", columns)
        self.assertNotIn("dtob_auto_now_add", columns)
        self.assertNotIn("tob_auto_now", columns)
        self.assertNotIn("tob_auto_now_add", columns)
        # Create a row
        Author.objects.create(name="Anonymous1")
        # Ensure fields were added with the correct defaults
        dob_auto_now = DateField(auto_now=True)
        dob_auto_now.set_attributes_from_name("dob_auto_now")
        self.check_added_field_default(
            editor,
            Author,
            dob_auto_now,
            "dob_auto_now",
            now.date(),
            cast_function=lambda x: x.date(),
        )
        dob_auto_now_add = DateField(auto_now_add=True)
        dob_auto_now_add.set_attributes_from_name("dob_auto_now_add")
        self.check_added_field_default(
            editor,
            Author,
            dob_auto_now_add,
            "dob_auto_now_add",
            now.date(),
            cast_function=lambda x: x.date(),
        )
        dtob_auto_now = DateTimeField(auto_now=True)
        dtob_auto_now.set_attributes_from_name("dtob_auto_now")
        self.check_added_field_default(
            editor,
            Author,
            dtob_auto_now,
            "dtob_auto_now",
            now,
        )
        dt_tm_of_birth_auto_now_add = DateTimeField(auto_now_add=True)
        dt_tm_of_birth_auto_now_add.set_attributes_from_name("dtob_auto_now_add")
        self.check_added_field_default(
            editor,
            Author,
            dt_tm_of_birth_auto_now_add,
            "dtob_auto_now_add",
            now,
        )
        tob_auto_now = TimeField(auto_now=True)
        tob_auto_now.set_attributes_from_name("tob_auto_now")
        self.check_added_field_default(
            editor,
            Author,
            tob_auto_now,
            "tob_auto_now",
            now.time(),
            cast_function=lambda x: x.time(),
        )
        tob_auto_now_add = TimeField(auto_now_add=True)
        tob_auto_now_add.set_attributes_from_name("tob_auto_now_add")
        self.check_added_field_default(
            editor,
            Author,
            tob_auto_now_add,
            "tob_auto_now_add",
            now.time(),
            cast_function=lambda x: x.time(),
        )