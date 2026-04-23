def forward(self, x1, x2):
        if self.two_conv:
            if self.use_torch_add:
                if self.with_bn:
                    x = torch.add(self.bn(self.conv(x1)), self.conv2(x1))
                else:
                    x = torch.add(self.conv(x1), self.conv2(x1))
            else:
                if self.with_bn:
                    x = self.bn(self.conv(x1)) + self.conv2(x1)
                else:
                    x = self.conv(x1) + self.conv2(x1)
        else:
            if self.use_torch_add:
                if self.left_conv:
                    if self.with_bn:
                        x = torch.add(self.bn(self.conv(x1)), x2)
                    else:
                        x = torch.add(self.conv(x1), x2)
                else:
                    if self.with_bn:
                        x = torch.add(x2, self.bn(self.conv(x1)))
                    else:
                        x = torch.add(x2, self.conv(x1))
            else:
                if self.left_conv:
                    if self.with_bn:
                        x = self.bn(self.conv(x1)) + x2
                    else:
                        x = self.conv(x1) + x2
                else:
                    if self.with_bn:
                        x = x2 + self.bn(self.conv(x1))
                    else:
                        x = x2 + self.conv(x1)
        if self.with_relu:
            x = self.relu(x)
        return x