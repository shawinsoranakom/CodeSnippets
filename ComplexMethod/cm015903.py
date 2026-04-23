def forward(self, x):
        inputs = [x.to(self.device) for i in range(10)]
        others = [x.to(self.device) for i in range(10)]
        clamp_input = [x.clamp(min=-1000.1, max=1000.1) for x in inputs]
        clamp_other = [x.clamp(min=-1000.1, max=1000.1) for x in others]
        nan_to_num_input = [torch.nan_to_num(x, 0.0) for x in clamp_input]
        nan_to_num_other = [torch.nan_to_num(x, 0.0) for x in clamp_other]
        detach_input = [x.detach() for x in nan_to_num_input]
        detach_other = [x.detach() for x in nan_to_num_other]
        stack_input = torch.stack(detach_input, dim=0)
        stack_other = torch.stack(detach_other, dim=0)
        return torch.stack((stack_input, stack_other), dim=0)