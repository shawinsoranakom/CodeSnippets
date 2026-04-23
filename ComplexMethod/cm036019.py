def transformer_optimizer(c: NLPAutoRegressionConfigs):
    """
    ### Create custom optimizer with weight decay

    This code is taken from [minGPT](https://github.com/karpathy/minGPT).
    This applies weight decay only to weights of linear layers.
    """
    # Collect names of parameters to apply weight decay
    decay = set()
    for mn, m in c.model.named_modules():
        for pn, p in m.named_parameters():
            fpn = f'{mn}.{pn}' if mn else pn  # full param name

            if fpn.endswith('weight') and isinstance(m, nn.Linear):
                decay.add(fpn)

    # Get all the parameters
    param_dict = {pn: p for pn, p in c.model.named_parameters()}
    # Parameters that are not decayed
    no_decay = set(param_dict.keys()) - decay

    # create the pytorch optimizer object
    opt_groups = [
        {"params": [param_dict[pn] for pn in sorted(list(decay))], "weight_decay": c.weight_decay},
        {"params": [param_dict[pn] for pn in sorted(list(no_decay))], "weight_decay": 0.0},
    ]

    # Create a [configurable optimizer](../optimizers/configs.html#OptimizerConfigs),
    # so that we can change these simply by passing
    # a config dictionary.
    optimizer = OptimizerConfigs()

    # Set parameter groups for optimization.
    optimizer.parameters = opt_groups
    # Use [cosine decay optimizer](../optimizers/adam_warmup_cosine_decay.html).
    # This is what GPT uses.
    optimizer.optimizer = 'AdamWarmupCosineDecay'
    # Set model embedding size, required if we use [Noam optimizer](../optimizers/noam.html)
    # which has an exponential decay.
    optimizer.d_model = c.d_model
    # Set default weight decay.
    # This is not required since we set the weight decay in the parameter groups.
    optimizer.weight_decay = c.weight_decay
    # GPT uses a maximum learning rate of $6 \times 10^{-4}$.
    optimizer.learning_rate = 6e-4
    # $\beta_1 = 0.9, \beta_2 = 0.95$
    optimizer.betas = (0.9, 0.95)
    # $\epsilon = 10^{-8}$
    optimizer.eps = 1e-8
    # Weight decay is decoupled from gradients
    optimizer.weight_decouple = True
    # Total number of optimization steps for learning rate cosine decay
    optimizer.total_steps = c.epochs * len(c.text.train) // (c.batch_size * c.seq_len)
    # Number of warmup optimization steps
    optimizer.warmup = c.warmup_steps // (c.batch_size * c.seq_len)

    return optimizer