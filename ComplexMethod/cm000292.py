def main():
    """This function starts execution phase"""
    while True:
        print(" Linear Discriminant Analysis ".center(50, "*"))
        print("*" * 50, "\n")
        print("First of all we should specify the number of classes that")
        print("we want to generate as training dataset")
        # Trying to get number of classes
        n_classes = valid_input(
            input_type=int,
            condition=lambda x: x > 0,
            input_msg="Enter the number of classes (Data Groupings): ",
            err_msg="Number of classes should be positive!",
        )

        print("-" * 100)

        # Trying to get the value of standard deviation
        std_dev = valid_input(
            input_type=float,
            condition=lambda x: x >= 0,
            input_msg=(
                "Enter the value of standard deviation"
                "(Default value is 1.0 for all classes): "
            ),
            err_msg="Standard deviation should not be negative!",
            default="1.0",
        )

        print("-" * 100)

        # Trying to get number of instances in classes and theirs means to generate
        # dataset
        counts = []  # An empty list to store instance counts of classes in dataset
        for i in range(n_classes):
            user_count = valid_input(
                input_type=int,
                condition=lambda x: x > 0,
                input_msg=(f"Enter The number of instances for class_{i + 1}: "),
                err_msg="Number of instances should be positive!",
            )
            counts.append(user_count)
        print("-" * 100)

        # An empty list to store values of user-entered means of classes
        user_means = []
        for a in range(n_classes):
            user_mean = valid_input(
                input_type=float,
                input_msg=(f"Enter the value of mean for class_{a + 1}: "),
                err_msg="This is an invalid value.",
            )
            user_means.append(user_mean)
        print("-" * 100)

        print("Standard deviation: ", std_dev)
        # print out the number of instances in classes in separated line
        for i, count in enumerate(counts, 1):
            print(f"Number of instances in class_{i} is: {count}")
        print("-" * 100)

        # print out mean values of classes separated line
        for i, user_mean in enumerate(user_means, 1):
            print(f"Mean of class_{i} is: {user_mean}")
        print("-" * 100)

        # Generating training dataset drawn from gaussian distribution
        x = [
            gaussian_distribution(user_means[j], std_dev, counts[j])
            for j in range(n_classes)
        ]
        print("Generated Normal Distribution: \n", x)
        print("-" * 100)

        # Generating Ys to detecting corresponding classes
        y = y_generator(n_classes, counts)
        print("Generated Corresponding Ys: \n", y)
        print("-" * 100)

        # Calculating the value of actual mean for each class
        actual_means = [calculate_mean(counts[k], x[k]) for k in range(n_classes)]
        # for loop iterates over number of elements in 'actual_means' list and print
        # out them in separated line
        for i, actual_mean in enumerate(actual_means, 1):
            print(f"Actual(Real) mean of class_{i} is: {actual_mean}")
        print("-" * 100)

        # Calculating the value of probabilities for each class
        probabilities = [
            calculate_probabilities(counts[i], sum(counts)) for i in range(n_classes)
        ]

        # for loop iterates over number of elements in 'probabilities' list and print
        # out them in separated line
        for i, probability in enumerate(probabilities, 1):
            print(f"Probability of class_{i} is: {probability}")
        print("-" * 100)

        # Calculating the values of variance for each class
        variance = calculate_variance(x, actual_means, sum(counts))
        print("Variance: ", variance)
        print("-" * 100)

        # Predicting Y values
        # storing predicted Y values in 'pre_indexes' variable
        pre_indexes = predict_y_values(x, actual_means, variance, probabilities)
        print("-" * 100)

        # Calculating Accuracy of the model
        print(f"Accuracy: {accuracy(y, pre_indexes)}")
        print("-" * 100)
        print(" DONE ".center(100, "+"))

        if input("Press any key to restart or 'q' for quit: ").strip().lower() == "q":
            print("\n" + "GoodBye!".center(100, "-") + "\n")
            break
        system("cls" if name == "nt" else "clear")