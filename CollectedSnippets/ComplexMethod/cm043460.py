def reshape_classifier_output(model, n=1000):
    """Reshapes last layer of model to match class count 'n', supporting Classify, Linear, Sequential types."""
    from models.common import Classify

    name, m = list((model.model if hasattr(model, "model") else model).named_children())[-1]  # last module
    if isinstance(m, Classify):  # YOLOv5 Classify() head
        if m.linear.out_features != n:
            m.linear = nn.Linear(m.linear.in_features, n)
    elif isinstance(m, nn.Linear):  # ResNet, EfficientNet
        if m.out_features != n:
            setattr(model, name, nn.Linear(m.in_features, n))
    elif isinstance(m, nn.Sequential):
        types = [type(x) for x in m]
        if nn.Linear in types:
            i = len(types) - 1 - types[::-1].index(nn.Linear)  # last nn.Linear index
            if m[i].out_features != n:
                m[i] = nn.Linear(m[i].in_features, n)
        elif nn.Conv2d in types:
            i = len(types) - 1 - types[::-1].index(nn.Conv2d)  # last nn.Conv2d index
            if m[i].out_channels != n:
                m[i] = nn.Conv2d(m[i].in_channels, n, m[i].kernel_size, m[i].stride, bias=m[i].bias is not None)