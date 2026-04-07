def decorator(view):
    view.is_decorated = True
    return view