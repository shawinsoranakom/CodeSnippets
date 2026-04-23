def run_folder(self, input, vocal_root, others_root, format):
        self.model.eval()
        path = input
        os.makedirs(vocal_root, exist_ok=True)
        os.makedirs(others_root, exist_ok=True)
        file_base_name = os.path.splitext(os.path.basename(path))[0]

        sample_rate = 44100
        if "sample_rate" in self.config["audio"]:
            sample_rate = self.config["audio"]["sample_rate"]

        try:
            mix, sr = librosa.load(path, sr=sample_rate, mono=False)
        except Exception as e:
            print("Can read track: {}".format(path))
            print("Error message: {}".format(str(e)))
            return

        # in case if model only supports mono tracks
        isstereo = self.config["model"].get("stereo", True)
        if not isstereo and len(mix.shape) != 1:
            mix = np.mean(mix, axis=0)  # if more than 2 channels, take mean
            print("Warning: Track has more than 1 channels, but model is mono, taking mean of all channels.")

        mix_orig = mix.copy()

        mixture = torch.tensor(mix, dtype=torch.float32)
        res = self.demix_track(self.model, mixture, self.device)

        if self.config["training"]["target_instrument"] is not None:
            # if target instrument is specified, save target instrument as vocal and other instruments as others
            # other instruments are caculated by subtracting target instrument from mixture
            target_instrument = self.config["training"]["target_instrument"]
            other_instruments = [i for i in self.config["training"]["instruments"] if i != target_instrument]
            other = mix_orig - res[target_instrument]  # caculate other instruments

            path_vocal = "{}/{}_{}.wav".format(vocal_root, file_base_name, target_instrument)
            path_other = "{}/{}_{}.wav".format(others_root, file_base_name, other_instruments[0])
            self.save_audio(path_vocal, res[target_instrument].T, sr, format)
            self.save_audio(path_other, other.T, sr, format)
        else:
            # if target instrument is not specified, save the first instrument as vocal and the rest as others
            vocal_inst = self.config["training"]["instruments"][0]
            path_vocal = "{}/{}_{}.wav".format(vocal_root, file_base_name, vocal_inst)
            self.save_audio(path_vocal, res[vocal_inst].T, sr, format)
            for other in self.config["training"]["instruments"][1:]:  # save other instruments
                path_other = "{}/{}_{}.wav".format(others_root, file_base_name, other)
                self.save_audio(path_other, res[other].T, sr, format)