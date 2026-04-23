def build_optimizer(self, model, name="auto", lr=0.001, momentum=0.9, decay=1e-5, iterations=1e5):
        """Construct an optimizer for the given model.

        Args:
            model (torch.nn.Module): The model for which to build an optimizer.
            name (str, optional): The name of the optimizer to use. If 'auto', the optimizer is selected based on the
                number of iterations.
            lr (float, optional): The learning rate for the optimizer.
            momentum (float, optional): The momentum factor for the optimizer.
            decay (float, optional): The weight decay for the optimizer.
            iterations (float, optional): The number of iterations, which determines the optimizer if name is 'auto'.

        Returns:
            (torch.optim.Optimizer): The constructed optimizer.
        """
        g = [{}, {}, {}, {}]  # optimizer parameter groups
        bn = tuple(v for k, v in nn.__dict__.items() if "Norm" in k)  # normalization layers, i.e. BatchNorm2d()
        if name == "auto":
            LOGGER.info(
                f"{colorstr('optimizer:')} 'optimizer=auto' found, "
                f"ignoring 'lr0={self.args.lr0}' and 'momentum={self.args.momentum}' and "
                f"determining best 'optimizer', 'lr0' and 'momentum' automatically... "
            )
            nc = self.data.get("nc", 10)  # number of classes
            lr_fit = round(0.002 * 5 / (4 + nc), 6)  # lr0 fit equation to 6 decimal places
            name, lr, momentum = ("MuSGD", 0.01, 0.9) if iterations > 10000 else ("AdamW", lr_fit, 0.9)
            self.args.warmup_bias_lr = 0.0  # no higher than 0.01 for Adam

        use_muon = name == "MuSGD"
        for module_name, module in unwrap_model(model).named_modules():
            for param_name, param in module.named_parameters(recurse=False):
                fullname = f"{module_name}.{param_name}" if module_name else param_name
                if param.ndim >= 2 and use_muon:
                    g[3][fullname] = param  # muon params
                elif "bias" in fullname:  # bias (no decay)
                    g[2][fullname] = param
                elif isinstance(module, bn) or "logit_scale" in fullname:  # weight (no decay)
                    # ContrastiveHead and BNContrastiveHead included here with 'logit_scale'
                    g[1][fullname] = param
                else:  # weight (with decay)
                    g[0][fullname] = param
        if not use_muon:
            g = [x.values() for x in g[:3]]  # convert to list of params

        optimizers = {"Adam", "Adamax", "AdamW", "NAdam", "RAdam", "RMSProp", "SGD", "MuSGD", "auto"}
        name = {x.lower(): x for x in optimizers}.get(name.lower())
        if name in {"Adam", "Adamax", "AdamW", "NAdam", "RAdam"}:
            optim_args = dict(lr=lr, betas=(momentum, 0.999), weight_decay=0.0)
        elif name == "RMSProp":
            optim_args = dict(lr=lr, momentum=momentum)
        elif name == "SGD" or name == "MuSGD":
            optim_args = dict(lr=lr, momentum=momentum, nesterov=True)
        else:
            raise NotImplementedError(
                f"Optimizer '{name}' not found in list of available optimizers {optimizers}. "
                "Request support for addition optimizers at https://github.com/ultralytics/ultralytics."
            )

        num_params = [len(g[0]), len(g[1]), len(g[2])]  # number of param groups
        g[2] = {"params": g[2], **optim_args, "param_group": "bias"}
        g[0] = {"params": g[0], **optim_args, "weight_decay": decay, "param_group": "weight"}
        g[1] = {"params": g[1], **optim_args, "weight_decay": 0.0, "param_group": "bn"}
        muon, sgd = (0.2, 1.0)
        if use_muon:
            num_params[0] = len(g[3])  # update number of params
            g[3] = {"params": g[3], **optim_args, "weight_decay": decay, "use_muon": True, "param_group": "muon"}
            import re

            # higher lr for certain parameters in MuSGD when funetuning
            pattern = re.compile(r"(?=.*23)(?=.*cv3)|proto\.semseg")
            g_ = []  # new param groups
            for x in g:
                p = x.pop("params")
                p1 = [v for k, v in p.items() if pattern.search(k)]
                p2 = [v for k, v in p.items() if not pattern.search(k)]
                g_.extend([{"params": p1, **x, "lr": lr * 3}, {"params": p2, **x}])
            g = g_
        optimizer = getattr(optim, name, partial(MuSGD, muon=muon, sgd=sgd))(params=g)

        LOGGER.info(
            f"{colorstr('optimizer:')} {type(optimizer).__name__}(lr={lr}, momentum={momentum}) with parameter groups "
            f"{num_params[1]} weight(decay=0.0), {num_params[0]} weight(decay={decay}), {num_params[2]} bias(decay=0.0)"
        )
        return optimizer