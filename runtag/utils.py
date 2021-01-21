def prompt(message, allowed=''):
    allowed = list(allowed)
    allowed_as_lower = list(map(str.lower, allowed))

    while True:
        typed = input('{message}{allowed}: '.format(
            message=message,
            allowed=f' ({"/".join(allowed)})' if allowed else '')).lower()

        if typed in allowed_as_lower:
            break

    return allowed[allowed_as_lower.index(typed)]

def l1_distance(left, right):
    return abs(left.x - right.x) + abs(left.y - right.y)