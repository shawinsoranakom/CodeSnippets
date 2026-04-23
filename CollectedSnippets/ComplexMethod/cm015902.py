def forward(self, x):
        inputs = torch.ops.aten.split(x.to(self.device), 500, dim=1)
        x_split = torch.ops.aten.split(inputs[0].to(self.device), 50, dim=1)
        y_split = torch.ops.aten.split(inputs[1].to(self.device), 50, dim=1)
        tanh_1 = [torch.ops.aten.tanh(x_split[i]) for i in range(len(x_split))]
        tanh_2 = [torch.ops.aten.tanh(y_split[i]) for i in range(len(y_split))]
        sigmoid_1 = [torch.ops.aten.sigmoid(tanh_1[i]) for i in range(len(tanh_1))]
        sigmoid_2 = [torch.ops.aten.sigmoid(tanh_2[i]) for i in range(len(tanh_2))]
        relu_1 = [torch.ops.aten.relu(sigmoid_1[i]) for i in range(len(sigmoid_1))]
        relu_2 = [torch.ops.aten.relu(sigmoid_2[i]) for i in range(len(sigmoid_2))]
        add = [torch.ops.aten.add(relu_1[i], relu_2[i]) for i in range(len(relu_1))]
        return torch.cat(add, dim=1)