def forward(self, x):
        inputs = torch.split(x.to(self.device), 500, dim=1)
        x_split = torch.split(inputs[0].to(self.device), 50, dim=1)
        y_split = torch.split(inputs[1].to(self.device), 50, dim=1)
        sigmoid_1 = [torch.sigmoid(x_split[i]) for i in range(len(x_split))]
        sigmoid_2 = [torch.sigmoid(y_split[i]) for i in range(len(y_split))]
        relu_1 = [torch.nn.functional.relu(sigmoid_1[i]) for i in range(len(sigmoid_1))]
        relu_2 = [torch.nn.functional.relu(sigmoid_2[i]) for i in range(len(sigmoid_2))]
        add = [torch.add(relu_1[i], relu_2[i]) for i in range(len(relu_1))]
        mul = [torch.mul(add[i], add[i]) for i in range(len(add))]
        sub = [torch.sub(mul[i], mul[i]) for i in range(len(mul))]
        div = [torch.div(sub[i], sub[i]) for i in range(len(sub))]
        return torch.cat(div, dim=1)