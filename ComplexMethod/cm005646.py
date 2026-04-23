def postprocess(self, audio):
        needs_decoding = False
        if isinstance(audio, dict):
            if "audio" in audio:
                audio = audio["audio"]
            else:
                needs_decoding = True
                audio = audio["sequences"]
        elif isinstance(audio, tuple):
            audio = audio[0]

        if needs_decoding and self.processor is not None:
            audio = self.processor.decode(audio)

        if isinstance(audio, list):
            audio = [el.to(device="cpu", dtype=torch.float).numpy().squeeze() for el in audio]
            audio = audio if len(audio) > 1 else audio[0]
        else:
            audio = audio.to(device="cpu", dtype=torch.float).numpy().squeeze()

        return AudioOutput(
            audio=audio,
            sampling_rate=self.sampling_rate,
        )