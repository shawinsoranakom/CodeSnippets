def validate(rank, a, h, loader, mode="seen"):
        assert rank == 0, "validate should only run on rank=0"
        generator.eval()
        torch.cuda.empty_cache()

        val_err_tot = 0
        val_pesq_tot = 0
        val_mrstft_tot = 0

        # Modules for evaluation metrics
        pesq_resampler = ta.transforms.Resample(h.sampling_rate, 16000).cuda()
        loss_mrstft = auraloss.freq.MultiResolutionSTFTLoss(device="cuda")

        if a.save_audio:  # Also save audio to disk if --save_audio is set to True
            os.makedirs(
                os.path.join(a.checkpoint_path, "samples", f"gt_{mode}"),
                exist_ok=True,
            )
            os.makedirs(
                os.path.join(a.checkpoint_path, "samples", f"{mode}_{steps:08d}"),
                exist_ok=True,
            )

        with torch.no_grad():
            print(f"step {steps} {mode} speaker validation...")

            # Loop over validation set and compute metrics
            for j, batch in enumerate(tqdm(loader)):
                x, y, _, y_mel = batch
                y = y.to(device)
                if hasattr(generator, "module"):
                    y_g_hat = generator.module(x.to(device))
                else:
                    y_g_hat = generator(x.to(device))
                y_mel = y_mel.to(device, non_blocking=True)
                y_g_hat_mel = mel_spectrogram(
                    y_g_hat.squeeze(1),
                    h.n_fft,
                    h.num_mels,
                    h.sampling_rate,
                    h.hop_size,
                    h.win_size,
                    h.fmin,
                    h.fmax_for_loss,
                )
                min_t = min(y_mel.size(-1), y_g_hat_mel.size(-1))
                val_err_tot += F.l1_loss(y_mel[..., :min_t], y_g_hat_mel[..., :min_t]).item()

                # PESQ calculation. only evaluate PESQ if it's speech signal (nonspeech PESQ will error out)
                if "nonspeech" not in mode:  # Skips if the name of dataset (in mode string) contains "nonspeech"
                    # Resample to 16000 for pesq
                    y_16k = pesq_resampler(y)
                    y_g_hat_16k = pesq_resampler(y_g_hat.squeeze(1))
                    y_int_16k = (y_16k[0] * MAX_WAV_VALUE).short().cpu().numpy()
                    y_g_hat_int_16k = (y_g_hat_16k[0] * MAX_WAV_VALUE).short().cpu().numpy()
                    val_pesq_tot += pesq(16000, y_int_16k, y_g_hat_int_16k, "wb")

                # MRSTFT calculation
                min_t = min(y.size(-1), y_g_hat.size(-1))
                val_mrstft_tot += loss_mrstft(y_g_hat[..., :min_t], y[..., :min_t]).item()

                # Log audio and figures to Tensorboard
                if j % a.eval_subsample == 0:  # Subsample every nth from validation set
                    if steps >= 0:
                        sw.add_audio(f"gt_{mode}/y_{j}", y[0], steps, h.sampling_rate)
                        if a.save_audio:  # Also save audio to disk if --save_audio is set to True
                            save_audio(
                                y[0],
                                os.path.join(
                                    a.checkpoint_path,
                                    "samples",
                                    f"gt_{mode}",
                                    f"{j:04d}.wav",
                                ),
                                h.sampling_rate,
                            )
                        sw.add_figure(
                            f"gt_{mode}/y_spec_{j}",
                            plot_spectrogram(x[0]),
                            steps,
                        )

                    sw.add_audio(
                        f"generated_{mode}/y_hat_{j}",
                        y_g_hat[0],
                        steps,
                        h.sampling_rate,
                    )
                    if a.save_audio:  # Also save audio to disk if --save_audio is set to True
                        save_audio(
                            y_g_hat[0, 0],
                            os.path.join(
                                a.checkpoint_path,
                                "samples",
                                f"{mode}_{steps:08d}",
                                f"{j:04d}.wav",
                            ),
                            h.sampling_rate,
                        )
                    # Spectrogram of synthesized audio
                    y_hat_spec = mel_spectrogram(
                        y_g_hat.squeeze(1),
                        h.n_fft,
                        h.num_mels,
                        h.sampling_rate,
                        h.hop_size,
                        h.win_size,
                        h.fmin,
                        h.fmax,
                    )
                    sw.add_figure(
                        f"generated_{mode}/y_hat_spec_{j}",
                        plot_spectrogram(y_hat_spec.squeeze(0).cpu().numpy()),
                        steps,
                    )

                    """
                    Visualization of spectrogram difference between GT and synthesized audio, difference higher than 1 is clipped for better visualization.
                    """
                    spec_delta = torch.clamp(
                        torch.abs(x[0] - y_hat_spec.squeeze(0).cpu()),
                        min=1e-6,
                        max=1.0,
                    )
                    sw.add_figure(
                        f"delta_dclip1_{mode}/spec_{j}",
                        plot_spectrogram_clipped(spec_delta.numpy(), clip_max=1.0),
                        steps,
                    )

            val_err = val_err_tot / (j + 1)
            val_pesq = val_pesq_tot / (j + 1)
            val_mrstft = val_mrstft_tot / (j + 1)
            # Log evaluation metrics to Tensorboard
            sw.add_scalar(f"validation_{mode}/mel_spec_error", val_err, steps)
            sw.add_scalar(f"validation_{mode}/pesq", val_pesq, steps)
            sw.add_scalar(f"validation_{mode}/mrstft", val_mrstft, steps)

        generator.train()