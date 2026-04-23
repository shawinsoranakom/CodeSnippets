def prediction(self, m, vocal_root, others_root, format):
        os.makedirs(vocal_root, exist_ok=True)
        os.makedirs(others_root, exist_ok=True)
        basename = os.path.basename(m)
        mix, rate = librosa.load(m, mono=False, sr=44100)
        if mix.ndim == 1:
            mix = np.asfortranarray([mix, mix])
        mix = mix.T
        sources = self.demix(mix.T)
        opt = sources[0].T
        if format in ["wav", "flac"]:
            sf.write("%s/%s_main_vocal.%s" % (vocal_root, basename, format), mix - opt, rate)
            sf.write("%s/%s_others.%s" % (others_root, basename, format), opt, rate)
        else:
            path_vocal = "%s/%s_main_vocal.wav" % (vocal_root, basename)
            path_other = "%s/%s_others.wav" % (others_root, basename)
            sf.write(path_vocal, mix - opt, rate)
            sf.write(path_other, opt, rate)
            opt_path_vocal = path_vocal[:-4] + ".%s" % format
            opt_path_other = path_other[:-4] + ".%s" % format
            if os.path.exists(path_vocal):
                os.system('ffmpeg -i "%s" -vn "%s" -q:a 2 -y' % (path_vocal, opt_path_vocal))
                if os.path.exists(opt_path_vocal):
                    try:
                        os.remove(path_vocal)
                    except:
                        pass
            if os.path.exists(path_other):
                os.system('ffmpeg -i "%s" -vn "%s" -q:a 2 -y' % (path_other, opt_path_other))
                if os.path.exists(opt_path_other):
                    try:
                        os.remove(path_other)
                    except:
                        pass