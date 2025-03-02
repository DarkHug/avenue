import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from system.models import Fixation

logger = logging.getLogger(__name__)


@shared_task
def check_and_delete_expired_fixations():
    from system.models import Fixation, Apartment

    current_time = timezone.now()
    logger.info(f"Запуск проверки истекших фиксаций: {current_time}")

    # Получаем все истекшие активные фиксации
    expired_fixations = Fixation.objects.filter(
        expires_at__lt=current_time,
        status="ACTIVE"
    )

    # Сохраняем уникальные идентификаторы квартир до удаления фиксаций
    affected_apartments = {}
    for fixation in expired_fixations:
        affected_apartments[fixation.apartment.id] = fixation.apartment

    # Используем транзакцию для обеспечения атомарности операций
    with transaction.atomic():
        count = expired_fixations.count()
        if count > 0:
            logger.info(f"Найдено {count} истекших фиксаций, удаляю...")
            expired_fixations.delete()
            logger.info(f"Успешно удалено {count} фиксаций")

            # Обработка очереди для каждой затронутой квартиры
            for apartment_id, apartment in affected_apartments.items():
                try:
                    logger.info(f"Обработка очереди для квартиры: {apartment.object}")

                    # Получаем текущее количество активных фиксаций
                    active_count = Fixation.objects.filter(
                        apartment__id=apartment.id,
                        status="ACTIVE"
                    ).count()
                    logger.info(f"Текущее количество активных фиксаций: {active_count}")

                    # Определяем, сколько фиксаций можем перевести из очереди в активные
                    slots_available = 3 - active_count
                    logger.info(f"Доступно слотов для активации: {slots_available}")

                    if slots_available > 0:
                        # Находим фиксации в очереди, отсортированные по дате создания (FIFO)
                        queue_fixations = Fixation.objects.filter(
                            apartment__id=apartment.id,  # Используем unique_id
                            status="QUEUE"
                        ).order_by('created_at')[:slots_available]

                        queue_count = queue_fixations.count()
                        logger.info(f"Найдено {queue_count} фиксаций в очереди для активации")

                        # Обновляем статус для фиксаций из очереди
                        updated_count = 0
                        for fix in queue_fixations:
                            logger.info(f"Активация фиксации {fix.id}")
                            fix.status = "ACTIVE"
                            fix.expires_at = timezone.now() + timezone.timedelta(days=3)
                            fix.save()
                            updated_count += 1

                        if updated_count > 0:
                            logger.info(f"Переведено {updated_count} фиксаций из очереди в активные для квартиры {apartment.object}")
                        else:
                            logger.info(f"Нет фиксаций для активации для квартиры {apartment.object}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке квартиры {apartment_id}: {str(e)}")

        else:
            logger.info("Истекших фиксаций не найдено")

    return f"Удалено {count} истекших фиксаций, обработаны очереди для {len(affected_apartments)} квартир"