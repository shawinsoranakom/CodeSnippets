def test_dynamic_toggle(self):
        acc = torch.accelerator.current_accelerator()
        self.assertIsNotNone(acc)
        device = acc.type
        gpu_activity = getattr(ProfilerActivity, device.upper(), None)
        self.assertIsNotNone(gpu_activity)
        activities = [ProfilerActivity.CPU, gpu_activity]
        with profile(activities=activities) as p:
            with torch.profiler.record_function("test_user_annotation"):
                x, y = (torch.rand(4, 4).to(device) for _ in range(2))
                torch.add(x, y)

        self.assertTrue(any("aten" in e.name for e in p.events()))

        self.assertTrue(any(device in e.name.lower() for e in p.events()))

        self.assertTrue(any("kernel" in e.name.lower() for e in p.events()))

        with profile(activities=activities) as p1:
            p1.toggle_collection_dynamic(False, [gpu_activity])
            with torch.profiler.record_function("test_user_annotation"):
                x, y = (torch.rand(4, 4).to(device) for _ in range(2))
                torch.add(x, y)

        self.assertTrue(any("aten" in e.name for e in p1.events()))

        self.assertTrue(all(device not in e.name for e in p1.events()))

        self.assertTrue(all("kernel" not in e.name.lower() for e in p1.events()))

        with profile(activities=activities) as p2:
            p2.toggle_collection_dynamic(False, activities)
            with torch.profiler.record_function("test_user_annotation"):
                x, y = (torch.rand(4, 4).to(device) for _ in range(2))
                torch.add(x, y)
        self.assertTrue(len(p2.events()) == 0)