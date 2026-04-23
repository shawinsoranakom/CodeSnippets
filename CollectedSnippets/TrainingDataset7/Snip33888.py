def gen_partial_template(name, *args, **kwargs):
    if args or kwargs:
        extra = " ".join((args, *("{k}={v}" for k, v in kwargs.items()))) + " "
    else:
        extra = ""
    return (
        f"{{% partialdef {name} {extra}%}}TEST with {name}!{{% endpartialdef %}}"
        f"{{% partial {name} %}}"
    )