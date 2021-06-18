
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from website.utils import get_log_url_for_user


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int)

    def handle(self, *args, **kwargs):
        user = get_user_model().objects.get(id=kwargs['user_id'])
        url = get_log_url_for_user(user)

        print(f"\n\n* * * * * login link for {user.username} * * * * *\n\n")
        print(url)
        print("\n\n* * * * * * * * * * * * * * * * * *")
