def train_and_evaluate(
    rank,
    epoch,
    hps,
    nets,
    optims,
    schedulers,
    scaler,
    loaders,
    logger,
    writers,
):
    net_g, net_d = nets
    optim_g, optim_d = optims
    # scheduler_g, scheduler_d = schedulers
    train_loader, eval_loader = loaders
    if writers is not None:
        writer, writer_eval = writers

    train_loader.batch_sampler.set_epoch(epoch)
    global global_step

    net_g.train()
    # net_d.train()
    # for batch_idx, (
    #     ssl,
    #     ssl_lengths,
    #     spec,
    #     spec_lengths,
    #     y,
    #     y_lengths,
    #     text,
    #     text_lengths,
    # ) in enumerate(tqdm(train_loader)):
    for batch_idx, (ssl, spec, mel, ssl_lengths, spec_lengths, text, text_lengths, mel_lengths) in enumerate(
        tqdm(train_loader)
    ):
        if torch.cuda.is_available():
            spec, spec_lengths = (
                spec.cuda(
                    rank,
                    non_blocking=True,
                ),
                spec_lengths.cuda(
                    rank,
                    non_blocking=True,
                ),
            )
            mel, mel_lengths = mel.cuda(rank, non_blocking=True), mel_lengths.cuda(rank, non_blocking=True)
            ssl = ssl.cuda(rank, non_blocking=True)
            ssl.requires_grad = False
            # ssl_lengths = ssl_lengths.cuda(rank, non_blocking=True)
            text, text_lengths = (
                text.cuda(
                    rank,
                    non_blocking=True,
                ),
                text_lengths.cuda(
                    rank,
                    non_blocking=True,
                ),
            )
        else:
            spec, spec_lengths = spec.to(device), spec_lengths.to(device)
            mel, mel_lengths = mel.to(device), mel_lengths.to(device)
            ssl = ssl.to(device)
            ssl.requires_grad = False
            # ssl_lengths = ssl_lengths.cuda(rank, non_blocking=True)
            text, text_lengths = text.to(device), text_lengths.to(device)

        with autocast(enabled=hps.train.fp16_run):
            cfm_loss = net_g(
                ssl,
                spec,
                mel,
                ssl_lengths,
                spec_lengths,
                text,
                text_lengths,
                mel_lengths,
                use_grad_ckpt=hps.train.grad_ckpt,
            )
            loss_gen_all = cfm_loss
        optim_g.zero_grad()
        scaler.scale(loss_gen_all).backward()
        scaler.unscale_(optim_g)
        grad_norm_g = commons.clip_grad_value_(net_g.parameters(), None)
        scaler.step(optim_g)
        scaler.update()

        if rank == 0:
            if global_step % hps.train.log_interval == 0:
                lr = optim_g.param_groups[0]["lr"]
                # losses = [commit_loss,cfm_loss,mel_loss,loss_disc, loss_gen, loss_fm, loss_mel, loss_kl]
                losses = [cfm_loss]
                logger.info(
                    "Train Epoch: {} [{:.0f}%]".format(
                        epoch,
                        100.0 * batch_idx / len(train_loader),
                    )
                )
                logger.info([x.item() for x in losses] + [global_step, lr])

                scalar_dict = {"loss/g/total": loss_gen_all, "learning_rate": lr, "grad_norm_g": grad_norm_g}
                # image_dict = {
                #     "slice/mel_org": utils.plot_spectrogram_to_numpy(y_mel[0].data.cpu().numpy()),
                #     "slice/mel_gen": utils.plot_spectrogram_to_numpy(y_hat_mel[0].data.cpu().numpy()),
                #     "all/mel": utils.plot_spectrogram_to_numpy(mel[0].data.cpu().numpy()),
                #     "all/stats_ssl": utils.plot_spectrogram_to_numpy(stats_ssl[0].data.cpu().numpy()),
                # }
                utils.summarize(
                    writer=writer,
                    global_step=global_step,
                    # images=image_dict,
                    scalars=scalar_dict,
                )

            # if global_step % hps.train.eval_interval == 0:
            #     # evaluate(hps, net_g, eval_loader, writer_eval)
            #     utils.save_checkpoint(net_g, optim_g, hps.train.learning_rate, epoch,os.path.join(hps.s2_ckpt_dir, "G_{}.pth".format(global_step)),scaler)
            #     # utils.save_checkpoint(net_d, optim_d, hps.train.learning_rate, epoch,os.path.join(hps.s2_ckpt_dir, "D_{}.pth".format(global_step)),scaler)
            #     # keep_ckpts = getattr(hps.train, 'keep_ckpts', 3)
            #     # if keep_ckpts > 0:
            #     #     utils.clean_checkpoints(path_to_models=hps.s2_ckpt_dir, n_ckpts_to_keep=keep_ckpts, sort_by_time=True)

        global_step += 1
    if epoch % hps.train.save_every_epoch == 0 and rank == 0:
        if hps.train.if_save_latest == 0:
            utils.save_checkpoint(
                net_g,
                optim_g,
                hps.train.learning_rate,
                epoch,
                os.path.join(
                    "%s/logs_s2_%s" % (hps.data.exp_dir, hps.model.version),
                    "G_{}.pth".format(global_step),
                ),
            )
            # utils.save_checkpoint(
            #     net_d,
            #     optim_d,
            #     hps.train.learning_rate,
            #     epoch,
            #     os.path.join(
            #         "%s/logs_s2_%s" % (hps.data.exp_dir,hps.model.version), "D_{}.pth".format(global_step)
            #     ),
            # )
        else:
            utils.save_checkpoint(
                net_g,
                optim_g,
                hps.train.learning_rate,
                epoch,
                os.path.join(
                    "%s/logs_s2_%s" % (hps.data.exp_dir, hps.model.version),
                    "G_{}.pth".format(233333333333),
                ),
            )
            # utils.save_checkpoint(
            #     net_d,
            #     optim_d,
            #     hps.train.learning_rate,
            #     epoch,
            #     os.path.join(
            #         "%s/logs_s2_%s" % (hps.data.exp_dir,hps.model.version), "D_{}.pth".format(233333333333)
            #     ),
            # )
        if rank == 0 and hps.train.if_save_every_weights == True:
            if hasattr(net_g, "module"):
                ckpt = net_g.module.state_dict()
            else:
                ckpt = net_g.state_dict()
            logger.info(
                "saving ckpt %s_e%s:%s"
                % (
                    hps.name,
                    epoch,
                    savee(
                        ckpt,
                        hps.name + "_e%s_s%s" % (epoch, global_step),
                        epoch,
                        global_step,
                        hps,
                    ),
                )
            )

    if rank == 0:
        logger.info("====> Epoch: {}".format(epoch))