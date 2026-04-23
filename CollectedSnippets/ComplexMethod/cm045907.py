def __init__(self, act_type, inplace=True):
        super(Activation, self).__init__()
        act_type = act_type.lower()
        if act_type == "relu":
            self.act = nn.ReLU(inplace=inplace)
        elif act_type == "relu6":
            self.act = nn.ReLU6(inplace=inplace)
        elif act_type == "sigmoid":
            raise NotImplementedError
        elif act_type == "hard_sigmoid":
            self.act = Hsigmoid(
                inplace
            )  # nn.Hardsigmoid(inplace=inplace)#Hsigmoid(inplace)#
        elif act_type == "hard_swish" or act_type == "hswish":
            self.act = Hswish(inplace=inplace)
        elif act_type == "leakyrelu":
            self.act = nn.LeakyReLU(inplace=inplace)
        elif act_type == "gelu":
            self.act = GELU(inplace=inplace)
        elif act_type == "swish":
            self.act = Swish(inplace=inplace)
        else:
            raise NotImplementedError