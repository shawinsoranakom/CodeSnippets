def test_model_form(self):
        EventModelForm({"dt": "2011-09-01 13:20:30"}).save()
        e = Event.objects.get()
        self.assertEqual(e.dt, datetime.datetime(2011, 9, 1, 13, 20, 30))