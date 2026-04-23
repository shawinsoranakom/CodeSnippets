def call(self, inputs):
        if self.data_format == "channels_first":
            spatial_dims = list(inputs.shape[2:5])
        else:
            spatial_dims = list(inputs.shape[1:4])

        for index in range(0, 3):
            if spatial_dims[index] is None:
                continue
            spatial_dims[index] -= sum(self.cropping[index])
            if spatial_dims[index] <= 0:
                raise ValueError(
                    "Values in `cropping` argument should be smaller than the "
                    "corresponding spatial dimension of the input. Received: "
                    f"inputs.shape={inputs.shape}, cropping={self.cropping}"
                )

        if self.data_format == "channels_first":
            if (
                self.cropping[0][1]
                == self.cropping[1][1]
                == self.cropping[2][1]
                == 0
            ):
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] :,
                    self.cropping[2][0] :,
                ]
            elif self.cropping[0][1] == self.cropping[1][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] :,
                    self.cropping[2][0] : -self.cropping[2][1],
                ]
            elif self.cropping[1][1] == self.cropping[2][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] :,
                    self.cropping[2][0] :,
                ]
            elif self.cropping[0][1] == self.cropping[2][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] : -self.cropping[1][1],
                    self.cropping[2][0] :,
                ]
            elif self.cropping[0][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] : -self.cropping[1][1],
                    self.cropping[2][0] : -self.cropping[2][1],
                ]
            elif self.cropping[1][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] :,
                    self.cropping[2][0] : -self.cropping[2][1],
                ]
            elif self.cropping[2][1] == 0:
                return inputs[
                    :,
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] : -self.cropping[1][1],
                    self.cropping[2][0] :,
                ]
            return inputs[
                :,
                :,
                self.cropping[0][0] : -self.cropping[0][1],
                self.cropping[1][0] : -self.cropping[1][1],
                self.cropping[2][0] : -self.cropping[2][1],
            ]
        else:
            if (
                self.cropping[0][1]
                == self.cropping[1][1]
                == self.cropping[2][1]
                == 0
            ):
                return inputs[
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] :,
                    self.cropping[2][0] :,
                    :,
                ]
            elif self.cropping[0][1] == self.cropping[1][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] :,
                    self.cropping[2][0] : -self.cropping[2][1],
                    :,
                ]
            elif self.cropping[1][1] == self.cropping[2][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] :,
                    self.cropping[2][0] :,
                    :,
                ]
            elif self.cropping[0][1] == self.cropping[2][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] : -self.cropping[1][1],
                    self.cropping[2][0] :,
                    :,
                ]
            elif self.cropping[0][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] :,
                    self.cropping[1][0] : -self.cropping[1][1],
                    self.cropping[2][0] : -self.cropping[2][1],
                    :,
                ]
            elif self.cropping[1][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] :,
                    self.cropping[2][0] : -self.cropping[2][1],
                    :,
                ]
            elif self.cropping[2][1] == 0:
                return inputs[
                    :,
                    self.cropping[0][0] : -self.cropping[0][1],
                    self.cropping[1][0] : -self.cropping[1][1],
                    self.cropping[2][0] :,
                    :,
                ]
            return inputs[
                :,
                self.cropping[0][0] : -self.cropping[0][1],
                self.cropping[1][0] : -self.cropping[1][1],
                self.cropping[2][0] : -self.cropping[2][1],
                :,
            ]