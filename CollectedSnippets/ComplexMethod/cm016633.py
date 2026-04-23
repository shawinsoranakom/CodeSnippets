def __init__(self, channels=[320, 640, 1280, 1280], nums_rb=3, cin=64, ksize=3, sk=False, use_conv=True, xl=True):
        super(Adapter, self).__init__()
        self.unshuffle_amount = 8
        resblock_no_downsample = []
        resblock_downsample = [3, 2, 1]
        self.xl = xl
        if self.xl:
            self.unshuffle_amount = 16
            resblock_no_downsample = [1]
            resblock_downsample = [2]

        self.input_channels = cin // (self.unshuffle_amount * self.unshuffle_amount)
        self.unshuffle = nn.PixelUnshuffle(self.unshuffle_amount)
        self.channels = channels
        self.nums_rb = nums_rb
        self.body = []
        for i in range(len(channels)):
            for j in range(nums_rb):
                if (i in resblock_downsample) and (j == 0):
                    self.body.append(
                        ResnetBlock(channels[i - 1], channels[i], down=True, ksize=ksize, sk=sk, use_conv=use_conv))
                elif (i in resblock_no_downsample) and (j == 0):
                    self.body.append(
                        ResnetBlock(channels[i - 1], channels[i], down=False, ksize=ksize, sk=sk, use_conv=use_conv))
                else:
                    self.body.append(
                        ResnetBlock(channels[i], channels[i], down=False, ksize=ksize, sk=sk, use_conv=use_conv))
        self.body = nn.ModuleList(self.body)
        self.conv_in = nn.Conv2d(cin, channels[0], 3, 1, 1)