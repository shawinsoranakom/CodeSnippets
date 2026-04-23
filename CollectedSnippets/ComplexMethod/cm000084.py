def solution(limit: int = 999_966_663_333) -> int:
    """
    Computes the solution to the problem up to the specified limit
    >>> solution(1000)
    34825

    >>> solution(10_000)
    1134942

    >>> solution(100_000)
    36393008
    """
    primes_upper_bound = math.floor(math.sqrt(limit)) + 100
    primes = prime_sieve(primes_upper_bound)

    matches_sum = 0
    prime_index = 0
    last_prime = primes[prime_index]

    while (last_prime**2) <= limit:
        next_prime = primes[prime_index + 1]

        lower_bound = last_prime**2
        upper_bound = next_prime**2

        # Get numbers divisible by lps(current)
        current = lower_bound + last_prime
        while upper_bound > current <= limit:
            matches_sum += current
            current += last_prime

        # Reset the upper_bound
        while (upper_bound - next_prime) > limit:
            upper_bound -= next_prime

        # Add the numbers divisible by ups(current)
        current = upper_bound - next_prime
        while current > lower_bound:
            matches_sum += current
            current -= next_prime

        # Remove the numbers divisible by both ups and lps
        current = 0
        while upper_bound > current <= limit:
            if current <= lower_bound:
                # Increment the current number
                current += last_prime * next_prime
                continue

            if current > limit:
                break

            # Remove twice since it was added by both ups and lps
            matches_sum -= current * 2

            # Increment the current number
            current += last_prime * next_prime

        # Setup for next pair
        last_prime = next_prime
        prime_index += 1

    return matches_sum