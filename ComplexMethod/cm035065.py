def __call__(self, model):
        if self.group_lr:
            if self.training_step == "LF_2":
                import paddle

                if isinstance(model, paddle.DataParallel):  # multi gpu
                    mlm = model._layers.head.MLM_VRM.MLM.parameters()
                    pre_mlm_pp = (
                        model._layers.head.MLM_VRM.Prediction.pp_share.parameters()
                    )
                    pre_mlm_w = (
                        model._layers.head.MLM_VRM.Prediction.w_share.parameters()
                    )
                else:  # single gpu
                    mlm = model.head.MLM_VRM.MLM.parameters()
                    pre_mlm_pp = model.head.MLM_VRM.Prediction.pp_share.parameters()
                    pre_mlm_w = model.head.MLM_VRM.Prediction.w_share.parameters()

                total = []
                for param in mlm:
                    total.append(id(param))
                for param in pre_mlm_pp:
                    total.append(id(param))
                for param in pre_mlm_w:
                    total.append(id(param))

                group_base_params = [
                    param for param in model.parameters() if id(param) in total
                ]
                group_small_params = [
                    param for param in model.parameters() if id(param) not in total
                ]
                train_params = [
                    {"params": group_base_params},
                    {
                        "params": group_small_params,
                        "learning_rate": self.learning_rate.values[0] * 0.1,
                    },
                ]

            else:
                print("group lr currently only support VisionLAN in LF_2 training step")
                train_params = [
                    param for param in model.parameters() if param.trainable is True
                ]
        else:
            train_params = [
                param for param in model.parameters() if param.trainable is True
            ]

        opt = optim.Adam(
            learning_rate=self.learning_rate,
            beta1=self.beta1,
            beta2=self.beta2,
            epsilon=self.epsilon,
            weight_decay=self.weight_decay,
            grad_clip=self.grad_clip,
            name=self.name,
            lazy_mode=self.lazy_mode,
            parameters=train_params,
        )
        return opt