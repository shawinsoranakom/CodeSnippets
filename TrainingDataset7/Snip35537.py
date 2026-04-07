def assertDone(self, nums):
        self.assertNotified(nums)
        self.assertEqual(sorted(t.num for t in Thing.objects.all()), sorted(nums))