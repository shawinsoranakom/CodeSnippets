def extract_aime_answer(response: str) -> str:
    """Extract numerical answer from AIME response"""

    # AIME answers are integers from 0-999
    # Look for patterns like "The answer is 123" or just standalone numbers
    patterns = [
        r"(?:the )?(?:final )?answer is (\d{1,3})",
        r"(?:therefore|thus|so),?\s*(?:the )?(?:final )?answer is (\d{1,3})",
        r"\\boxed\{(\d{1,3})\}",
        r"\$\\boxed\{(\d{1,3})\}\$",
        r"(?:answer|result):\s*(\d{1,3})",
        r"(?:^|\n)\s*(\d{1,3})\s*(?:\n|$)",  # Standalone number
    ]

    response_lower = response.lower().strip()

    for pattern in patterns:
        matches = re.findall(pattern, response_lower, re.MULTILINE | re.IGNORECASE)
        if matches:
            # Get the last match (most likely to be final answer)
            answer = matches[-1]
            try:
                num = int(answer)
                if 0 <= num <= 999:  # AIME answers are in range 0-999
                    return str(num)
            except ValueError:
                continue

    # If no clear pattern found, try to extract any 1-3 digit number
    numbers = re.findall(r"\b(\d{1,3})\b", response)
    if numbers:
        for num_str in reversed(numbers):  # Check from end
            try:
                num = int(num_str)
                if 0 <= num <= 999:
                    return str(num)
            except ValueError:
                continue

    return ""