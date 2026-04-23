def train_and_evaluate(rank, epoch, hps, nets, optims, schedulers, scaler, loaders, logger, writers):
    net_g, net_d = nets
    optim_g, optim_d = optims
    # scheduler_g, scheduler_d = schedulers
    train_loader, eval_loader = loaders
    if writers is not None:
        writer, writer_eval = writers

    train_loader.batch_sampler.set_epoch(epoch)
    global global_step

    net_g.train()
    net_d.train()
    for batch_idx, data in enumerate(tqdm(train_loader)):
        if hps.model.version in {"v2Pro", "v2ProPlus"}:
            ssl, ssl_lengths, spec, spec_lengths, y, y_lengths, text, text_lengths, sv_emb = data
        else:
            ssl, ssl_lengths, spec, spec_lengths, y, y_lengths, text, text_lengths = data
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
            y, y_lengths = (
                y.cuda(
                    rank,
                    non_blocking=True,
                ),
                y_lengths.cuda(
                    rank,
                    non_blocking=True,
                ),
            )
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
            if hps.model.version in {"v2Pro", "v2ProPlus"}:
                sv_emb = sv_emb.cuda(rank, non_blocking=True)
        else:
            spec, spec_lengths = spec.to(device), spec_lengths.to(device)
            y, y_lengths = y.to(device), y_lengths.to(device)
            ssl = ssl.to(device)
            ssl.requires_grad = False
            # ssl_lengths = ssl_lengths.cuda(rank, non_blocking=True)
            text, text_lengths = text.to(device), text_lengths.to(device)
            if hps.model.version in {"v2Pro", "v2ProPlus"}:
                sv_emb = sv_emb.to(device)
        with autocast(enabled=hps.train.fp16_run):
            if hps.model.version in {"v2Pro", "v2ProPlus"}:
                (y_hat, kl_ssl, ids_slice, x_mask, z_mask, (z, z_p, m_p, logs_p, m_q, logs_q), stats_ssl) = net_g(
                    ssl, spec, spec_lengths, text, text_lengths, sv_emb
                )
            else:
                (
                    y_hat,
                    kl_ssl,
                    ids_slice,
                    x_mask,
                    z_mask,
                    (z, z_p, m_p, logs_p, m_q, logs_q),
                    stats_ssl,
                ) = net_g(ssl, spec, spec_lengths, text, text_lengths)

            mel = spec_to_mel_torch(
                spec,
                hps.data.filter_length,
                hps.data.n_mel_channels,
                hps.data.sampling_rate,
                hps.data.mel_fmin,
                hps.data.mel_fmax,
            )
            y_mel = commons.slice_segments(mel, ids_slice, hps.train.segment_size // hps.data.hop_length)
            y_hat_mel = mel_spectrogram_torch(
                y_hat.squeeze(1),
                hps.data.filter_length,
                hps.data.n_mel_channels,
                hps.data.sampling_rate,
                hps.data.hop_length,
                hps.data.win_length,
                hps.data.mel_fmin,
                hps.data.mel_fmax,
            )

            y = commons.slice_segments(y, ids_slice * hps.data.hop_length, hps.train.segment_size)  # slice

            # Discriminator
            y_d_hat_r, y_d_hat_g, _, _ = net_d(y, y_hat.detach())
            with autocast(enabled=False):
                loss_disc, losses_disc_r, losses_disc_g = discriminator_loss(
                    y_d_hat_r,
                    y_d_hat_g,
                )
                loss_disc_all = loss_disc
        optim_d.zero_grad()
        scaler.scale(loss_disc_all).backward()
        scaler.unscale_(optim_d)
        grad_norm_d = commons.clip_grad_value_(net_d.parameters(), None)
        scaler.step(optim_d)

        with autocast(enabled=hps.train.fp16_run):
            # Generator
            y_d_hat_r, y_d_hat_g, fmap_r, fmap_g = net_d(y, y_hat)
            with autocast(enabled=False):
                loss_mel = F.l1_loss(y_mel, y_hat_mel) * hps.train.c_mel
                loss_kl = kl_loss(z_p, logs_q, m_p, logs_p, z_mask) * hps.train.c_kl

                loss_fm = feature_loss(fmap_r, fmap_g)
                loss_gen, losses_gen = generator_loss(y_d_hat_g)
                loss_gen_all = loss_gen + loss_fm + loss_mel + kl_ssl * 1 + loss_kl

        optim_g.zero_grad()
        scaler.scale(loss_gen_all).backward()
        scaler.unscale_(optim_g)
        grad_norm_g = commons.clip_grad_value_(net_g.parameters(), None)
        scaler.step(optim_g)
        scaler.update()

        if rank == 0:
            if global_step % hps.train.log_interval == 0:
                lr = optim_g.param_groups[0]["lr"]
                losses = [loss_disc, loss_gen, loss_fm, loss_mel, kl_ssl, loss_kl]
                logger.info(
                    "Train Epoch: {} [{:.0f}%]".format(
                        epoch,
                        100.0 * batch_idx / len(train_loader),
                    )
                )
                logger.info([x.item() for x in losses] + [global_step, lr])

                scalar_dict = {
                    "loss/g/total": loss_gen_all,
                    "loss/d/total": loss_disc_all,
                    "learning_rate": lr,
                    "grad_norm_d": grad_norm_d,
                    "grad_norm_g": grad_norm_g,
                }
                scalar_dict.update(
                    {
                        "loss/g/fm": loss_fm,
                        "loss/g/mel": loss_mel,
                        "loss/g/kl_ssl": kl_ssl,
                        "loss/g/kl": loss_kl,
                    }
                )

                # scalar_dict.update({"loss/g/{}".format(i): v for i, v in enumerate(losses_gen)})
                # scalar_dict.update({"loss/d_r/{}".format(i): v for i, v in enumerate(losses_disc_r)})
                # scalar_dict.update({"loss/d_g/{}".format(i): v for i, v in enumerate(losses_disc_g)})
                image_dict = None
                try:  ###Some people installed the wrong version of matplotlib.
                    image_dict = {
                        "slice/mel_org": utils.plot_spectrogram_to_numpy(
                            y_mel[0].data.cpu().numpy(),
                        ),
                        "slice/mel_gen": utils.plot_spectrogram_to_numpy(
                            y_hat_mel[0].data.cpu().numpy(),
                        ),
                        "all/mel": utils.plot_spectrogram_to_numpy(
                            mel[0].data.cpu().numpy(),
                        ),
                        "all/stats_ssl": utils.plot_spectrogram_to_numpy(
                            stats_ssl[0].data.cpu().numpy(),
                        ),
                    }
                except:
                    pass
                if image_dict:
                    utils.summarize(
                        writer=writer,
                        global_step=global_step,
                        images=image_dict,
                        scalars=scalar_dict,
                    )
                else:
                    utils.summarize(
                        writer=writer,
                        global_step=global_step,
                        scalars=scalar_dict,
                    )
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
            utils.save_checkpoint(
                net_d,
                optim_d,
                hps.train.learning_rate,
                epoch,
                os.path.join(
                    "%s/logs_s2_%s" % (hps.data.exp_dir, hps.model.version),
                    "D_{}.pth".format(global_step),
                ),
            )
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
            utils.save_checkpoint(
                net_d,
                optim_d,
                hps.train.learning_rate,
                epoch,
                os.path.join(
                    "%s/logs_s2_%s" % (hps.data.exp_dir, hps.model.version),
                    "D_{}.pth".format(233333333333),
                ),
            )
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
                        model_version=None if hps.model.version not in {"v2Pro", "v2ProPlus"} else hps.model.version,
                    ),
                )
            )

    if rank == 0:
        logger.info("====> Epoch: {}".format(epoch))