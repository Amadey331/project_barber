from datetime import date,datetime

# Чтоб дату выбодить красиво




# формат: Вт, 30 мая
def format_date_rus(date_obj: datetime) -> str:
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    weekday = weekdays[date_obj.weekday()]
    day = date_obj.day
    month = months[date_obj.month - 1]
    return f"{weekday}, {day} {month}"  





def format_rating(rating_sum: int, rating_count: int) -> str:
    if rating_count == 0:
        return "Рейтинг: — (нет оценок)"
    
    average = rating_sum / rating_count
    full_stars = int(average)             # Кол-во полных звёзд
    half_star = 1 if average - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    stars_str = "★" * full_stars + "½" * half_star + "☆" * empty_stars
    return f"Рейтинг: {stars_str} ({rating_count})"