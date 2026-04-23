def __init__(self, scale=None, mean=None, std=None, order='chw', **kwargs):
        if isinstance(scale, str):
            try:
                scale = float(scale)
            except ValueError:
                if '/' in scale:
                    parts = scale.split('/')
                    scale = ast.literal_eval(parts[0]) / ast.literal_eval(parts[1])
                else:
                    scale = ast.literal_eval(scale)
        self.scale = np.float32(scale if scale is not None else 1.0 / 255.0)
        mean = mean if mean is not None else [0.485, 0.456, 0.406]
        std = std if std is not None else [0.229, 0.224, 0.225]

        shape = (3, 1, 1) if order == 'chw' else (1, 1, 3)
        self.mean = np.array(mean).reshape(shape).astype('float32')
        self.std = np.array(std).reshape(shape).astype('float32')