def call(self, inputs):
        if self.data_format == "channels_first":
            if (
                inputs.shape[2] is not None
                and sum(self.cropping[0]) >= inputs.shape[2]
            ) or (
                inputs.shape[3] is not None
                and sum(self.cropping[1]) >= inputs.shape[3]
            ):
                raise ValueError(
                    "Values in `cropping` argument should be smaller than the "
                    "corresponding spatial dimension of the input. Received: "
                    f"inputs.shape={inputs.shape}, cropping={self.cropping}"
                )
            if self.cropping[0][1] == self.cropping[1][1] == 0:
                return inputs[
                    :, :, self.cropping[0][0] :, self.cropping[1][0] :
                ]
            elif self.cropping[0][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] : -self.cropping[1][1],
                ]
            elif self.cropping[1][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] :,
                ]
            return inputs[
                :,
                :,
                self.cropping[0][0] : -self.cropping[0][1],
                self.cropping[1][0] : -self.cropping[1][1],
            ]
        else:
            if (
                inputs.shape[1] is not None
                and sum(self.cropping[0]) >= inputs.shape[1]
            ) or (
                inputs.shape[2] is not None
                and sum(self.cropping[1]) >= inputs.shape[2]
            ):
                raise ValueError(
                    "Values in `cropping` argument should be smaller than the "
                    "corresponding spatial dimension of the input. Received: "
                    f"inputs.shape={inputs.shape}, cropping={self.cropping}"
                )
            if self.cropping[0][1] == self.cropping[1][1] == 0:
                return inputs[
                    :, self.cropping[0][0] :, self.cropping[1][0] :, :
                ]
            elif self.cropping[0][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] : -self.cropping[1][1],
                    :,
                ]
            elif self.cropping[1][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] :,
                    :,
                ]
            return inputs[
                :,
                self.cropping[0][0] : -self.cropping[0][1],
                self.cropping[1][0] : -self.cropping[1][1],
                :,
            ]