def getLocation():
    location = input(
        "Choose where to play. Enter two numbers separated by a comma [example: 1,1]: "
    )
    print(f"\nYou picked {location}")
    coordinates = [int(x) for x in location.split(",")]
    while (
        len(coordinates) != 2
        or coordinates[0] < 0
        or coordinates[0] > 2
        or coordinates[1] < 0
        or coordinates[1] > 2
    ):
        print("You inputted a location in an invalid format")
        location = input(
            "Choose where to play. Enter two numbers separated by a comma "
            "[example: 1,1]: "
        )
        coordinates = [int(x) for x in location.split(",")]
    return coordinates