def post_save_handler(signal, sender, instance, **kwargs):
            data.append("post_save signal, %s" % instance)
            if "created" in kwargs:
                if kwargs["created"]:
                    data.append("Is created")
                else:
                    data.append("Is updated")
            if kwargs.get("raw"):
                data.append("Is raw")