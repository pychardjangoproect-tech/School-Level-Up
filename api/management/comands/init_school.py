from django.core.management.base import BaseCommand
from api.models import ClassRoom


class Command(BaseCommand):
    help = 'Автоматически создает 8 классов для школы'

    def handle(self, *args, **kwargs):
        # Список классов, которые нужны по ТЗ
        classes = ['6В', '6Д', '7В', '7Д', '8В', '8Д', '9В', '9Д']

        for name in classes:
            # get_or_create создает класс, если его нет, или просто получает его
            ClassRoom.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS('✅ Все 8 классов успешно созданы!'))