def get_random_emoji() -> str:

    # Weigh our emojis 10x, cuz we're awesome!
    # TODO: fix the random seed with a hash of the user's app code, for stability?
    return random.choice(RANDOM_EMOJIS + 10 * ENG_EMOJIS)