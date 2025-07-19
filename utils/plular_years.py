
def plural_years(n: int) -> str:
    if 11 <= n % 100 <= 14:
        return f"{n} лет"
    elif n % 10 == 1:
        return f"{n} год"
    elif 2 <= n % 10 <= 4:
        return f"{n} года"
    else:
        return f"{n} лет"