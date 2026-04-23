def test_num_params(self):
        import torch.nn as nn
        import torch.nn.functional as F

        class ModelSimple(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv1 = nn.Conv2d(1, 20, 5)

            def forward(self, x):
                return F.relu(self.conv1(x))

        self.assertEqual([x.numel() for x in ModelSimple().parameters()], [500, 20])

        compilation_events = []
        with mock.patch("torch._dynamo.utils.log_compilation_event") as log_event:
            m = ModelSimple()
            torch.compile(m)(torch.randn(1, 10, 10))
            compilation_events = [arg[0][0] for arg in log_event.call_args_list]
        self.assertEqual(compilation_events[0].param_numel, 520)
        self.assertEqual(compilation_events[0].param_bytes, 4 * 520)
        self.assertEqual(compilation_events[0].param_count, 2)

        class ModelWrapped(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.m1 = ModelSimple()
                self.m2 = ModelSimple()

            def forward(self, x):
                return self.m1(x) + self.m2(x)

        compilation_events = []
        with mock.patch("torch._dynamo.utils.log_compilation_event") as log_event:
            m = ModelWrapped()
            torch.compile(m)(torch.randn(1, 10, 10))
            compilation_events = [arg[0][0] for arg in log_event.call_args_list]
        self.assertEqual(compilation_events[0].param_numel, 1040)
        self.assertEqual(compilation_events[0].param_bytes, 4 * 1040)
        self.assertEqual(compilation_events[0].param_count, 4)

        # Test a tied module
        l1 = nn.Linear(4, 4)
        l2 = nn.Linear(4, 4)
        m = nn.Sequential(l1, nn.Sequential(l1, l2))
        self.assertEqual([x.numel() for x in m.parameters()], [16, 4, 16, 4])
        with mock.patch("torch._dynamo.utils.log_compilation_event") as log_event:
            torch.compile(m)(torch.randn(4, 4))
            compilation_events = [arg[0][0] for arg in log_event.call_args_list]
        self.assertEqual(compilation_events[0].param_numel, 40)
        self.assertEqual(compilation_events[0].param_bytes, 4 * 40)
        self.assertEqual(compilation_events[0].param_count, 4)

        # Test tied weights
        l1 = nn.Linear(4, 4)
        l2 = nn.Linear(4, 4)
        l1.weight = l2.weight
        m = nn.Sequential(l1, nn.Sequential(l2))
        self.assertEqual([x.numel() for x in m.parameters()], [16, 4, 4])
        with mock.patch("torch._dynamo.utils.log_compilation_event") as log_event:
            torch.compile(m)(torch.randn(4, 4))
            compilation_events = [arg[0][0] for arg in log_event.call_args_list]
        self.assertEqual(compilation_events[0].param_numel, 24)
        self.assertEqual(compilation_events[0].param_bytes, 4 * 24)
        self.assertEqual(compilation_events[0].param_count, 3)