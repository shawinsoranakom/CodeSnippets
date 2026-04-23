def __call__(self, model):
        parameters = [param for param in model.parameters() if param.trainable is True]

        self.no_weight_decay_param_name_list = [
            p.name
            for n, p in model.named_parameters()
            if any(nd in n for nd in self.no_weight_decay_name_list)
        ]

        if self.one_dim_param_no_weight_decay:
            self.no_weight_decay_param_name_list += [
                p.name for n, p in model.named_parameters() if len(p.shape) == 1
            ]

        opt = optim.AdamW(
            learning_rate=self.learning_rate,
            beta1=self.beta1,
            beta2=self.beta2,
            epsilon=self.epsilon,
            parameters=parameters,
            weight_decay=self.weight_decay,
            multi_precision=self.multi_precision,
            grad_clip=self.grad_clip,
            name=self.name,
            lazy_mode=self.lazy_mode,
            apply_decay_param_fun=self._apply_decay_param_fun,
        )
        return opt