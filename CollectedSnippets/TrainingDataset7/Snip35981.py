def unraisablehook(unraisable):
                    unraisable_exceptions.append(unraisable)
                    sys.__unraisablehook__(unraisable)