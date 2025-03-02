from celery import shared_task
from django.utils import timezone
from system.models import Fixation


@shared_task
def check_and_delete_expired_fixations():
    """
    Задача для проверки и удаления истекших фиксаций.
    """
    current_time = timezone.now()

    # Получаем все истекшие фиксации
    expired_fixations = Fixation.objects.filter(expires_at__lt=current_time)

    # Логирование для отслеживания работы
    if expired_fixations.exists():
        count = expired_fixations.count()
        # Удаляем истекшие фиксации
        expired_fixations.delete()
        return f"Удалено {count} истекших фиксаций"
    else:
        return "Истекших фиксаций не найдено"
