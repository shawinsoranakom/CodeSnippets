def item_generator():
            yield "A"
            yield inner_generator()
            yield "D"