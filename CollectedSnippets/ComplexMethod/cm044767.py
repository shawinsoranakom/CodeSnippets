def run(rank, n_gpus, hps):
    global global_step, no_grad_names, save_root, lora_rank
    if rank == 0:
        logger = utils.get_logger(hps.data.exp_dir)
        logger.info(hps)
        # utils.check_git_hash(hps.s2_ckpt_dir)
        writer = SummaryWriter(log_dir=hps.s2_ckpt_dir)
        writer_eval = SummaryWriter(log_dir=os.path.join(hps.s2_ckpt_dir, "eval"))

    use_ddp = n_gpus > 1
    if use_ddp:
        dist.init_process_group(
            backend="gloo" if os.name == "nt" or not torch.cuda.is_available() else "nccl",
            init_method="env://?use_libuv=False",
            world_size=n_gpus,
            rank=rank,
        )
    torch.manual_seed(hps.train.seed)
    if torch.cuda.is_available():
        torch.cuda.set_device(rank)

    TextAudioSpeakerLoader = TextAudioSpeakerLoaderV3 if hps.model.version == "v3" else TextAudioSpeakerLoaderV4
    TextAudioSpeakerCollate = TextAudioSpeakerCollateV3 if hps.model.version == "v3" else TextAudioSpeakerCollateV4
    train_dataset = TextAudioSpeakerLoader(hps.data)  ########
    train_sampler = DistributedBucketSampler(
        train_dataset,
        hps.train.batch_size,
        [
            32,
            300,
            400,
            500,
            600,
            700,
            800,
            900,
            1000,
            # 1100,
            # 1200,
            # 1300,
            # 1400,
            # 1500,
            # 1600,
            # 1700,
            # 1800,
            # 1900,
        ],
        num_replicas=n_gpus,
        rank=rank,
        shuffle=True,
    )
    collate_fn = TextAudioSpeakerCollate()
    worker_count = 0 if os.name == "nt" and n_gpus <= 1 else min(2 if os.name == "nt" else 5, os.cpu_count() or 1)
    loader_kwargs = dict(
        num_workers=worker_count,
        shuffle=False,
        pin_memory=torch.cuda.is_available(),
        collate_fn=collate_fn,
        batch_sampler=train_sampler,
    )
    if worker_count > 0:
        loader_kwargs["persistent_workers"] = True
        loader_kwargs["prefetch_factor"] = 2 if os.name == "nt" else 3
    train_loader = DataLoader(
        train_dataset,
        **loader_kwargs,
    )
    save_root = "%s/logs_s2_%s_lora_%s" % (hps.data.exp_dir, hps.model.version, hps.train.lora_rank)
    os.makedirs(save_root, exist_ok=True)
    lora_rank = int(hps.train.lora_rank)
    lora_config = LoraConfig(
        target_modules=["to_k", "to_q", "to_v", "to_out.0"],
        r=lora_rank,
        lora_alpha=lora_rank,
        init_lora_weights=True,
    )

    def get_model(hps):
        return SynthesizerTrn(
            hps.data.filter_length // 2 + 1,
            hps.train.segment_size // hps.data.hop_length,
            n_speakers=hps.data.n_speakers,
            **hps.model,
        )

    def get_optim(net_g):
        return torch.optim.AdamW(
            filter(lambda p: p.requires_grad, net_g.parameters()),  ###默认所有层lr一致
            hps.train.learning_rate,
            betas=hps.train.betas,
            eps=hps.train.eps,
        )

    def model2cuda(net_g, rank):
        if torch.cuda.is_available():
            net_g = net_g.cuda(rank)
            if use_ddp:
                net_g = DDP(net_g, device_ids=[rank], find_unused_parameters=True)
        else:
            net_g = net_g.to(device)
        return net_g

    try:  # 如果能加载自动resume
        net_g = get_model(hps)
        net_g.cfm = get_peft_model(net_g.cfm, lora_config)
        net_g = model2cuda(net_g, rank)
        optim_g = get_optim(net_g)
        # _, _, _, epoch_str = utils.load_checkpoint(utils.latest_checkpoint_path(hps.model_dir, "G_*.pth"), net_g, optim_g,load_opt=0)
        _, _, _, epoch_str = utils.load_checkpoint(
            utils.latest_checkpoint_path(save_root, "G_*.pth"),
            net_g,
            optim_g,
        )
        epoch_str += 1
        global_step = (epoch_str - 1) * len(train_loader)
    except:  # 如果首次不能加载，加载pretrain
        # traceback.print_exc()
        epoch_str = 1
        global_step = 0
        net_g = get_model(hps)
        if (
            hps.train.pretrained_s2G != ""
            and hps.train.pretrained_s2G != None
            and os.path.exists(hps.train.pretrained_s2G)
        ):
            if rank == 0:
                logger.info("loaded pretrained %s" % hps.train.pretrained_s2G)
            print(
                "loaded pretrained %s" % hps.train.pretrained_s2G,
                net_g.load_state_dict(
                    torch.load(hps.train.pretrained_s2G, map_location="cpu", weights_only=False)["weight"],
                    strict=False,
                ),
            )
        net_g.cfm = get_peft_model(net_g.cfm, lora_config)
        net_g = model2cuda(net_g, rank)
        optim_g = get_optim(net_g)

    no_grad_names = set()
    for name, param in net_g.named_parameters():
        if not param.requires_grad:
            no_grad_names.add(name.replace("module.", ""))
            # print(name, "not requires_grad")
    # print(no_grad_names)
    # os._exit(233333)

    scheduler_g = torch.optim.lr_scheduler.ExponentialLR(optim_g, gamma=hps.train.lr_decay, last_epoch=-1)
    for _ in range(epoch_str):
        scheduler_g.step()

    scaler = GradScaler(enabled=hps.train.fp16_run)

    net_d = optim_d = scheduler_d = None
    print("start training from epoch %s" % epoch_str)
    for epoch in range(epoch_str, hps.train.epochs + 1):
        if rank == 0:
            train_and_evaluate(
                rank,
                epoch,
                hps,
                [net_g, net_d],
                [optim_g, optim_d],
                [scheduler_g, scheduler_d],
                scaler,
                # [train_loader, eval_loader], logger, [writer, writer_eval])
                [train_loader, None],
                logger,
                [writer, writer_eval],
            )
        else:
            train_and_evaluate(
                rank,
                epoch,
                hps,
                [net_g, net_d],
                [optim_g, optim_d],
                [scheduler_g, scheduler_d],
                scaler,
                [train_loader, None],
                None,
                None,
            )
        scheduler_g.step()
    if use_ddp and dist.is_initialized():
        dist.destroy_process_group()
    print("training done")