from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='auth')
        cls.new_user = User.objects.create(username='random_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описания',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.new_user)
        cache.clear()

    def test_pages_available_for_guest_user(self):
        """
        Проверяет доступность страниц для неавторизованных пользователей.
        """
        pages_adress = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PostURLTests.group.slug}
                    ),
            reverse('posts:profile',
                    kwargs={'username': PostURLTests.user}
                    ),
            reverse('posts:post_detail',
                    kwargs={'post_id': PostURLTests.post.id}
                    ),
        ]
        for pages in pages_adress:
            with self.subTest(pages_adress=pages_adress):
                response = self.client.get(pages)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexist_page_send_error(self):
        """
        Проверка выдачи ошибки при переходе на несуществующую страницу.
        """
        response = self.client.get('/unexist_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_guest_client_redirects(self):
        """
        Проверка переадресации неавторизованных пользователей.
        """
        login_url = reverse('users:login')
        url = reverse('posts:create_post')
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostURLTests.post.id}
        )
        follow_page = reverse('posts:follow_index')
        redirect_pages = {
            reverse('posts:create_post'): f'{login_url}?next={url}',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostURLTests.post.id}
            ): f'{login_url}?next={post_edit_url}',
            reverse('posts:follow_index'): f'{login_url}?next={follow_page}'
        }
        for pages, redirects in redirect_pages.items():
            with self.subTest(redirects=redirects):
                response = self.client.get(pages)
                self.assertRedirects(response, redirects)

    def test_available_pages_for_authorized_author_client(self):
        """
        Проверка доступности страниц для автора.
        """
        available_pages = [
            reverse('posts:create_post'),
            reverse('posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.id}
                    ),
            reverse('posts:follow_index'),
        ]
        for pages in available_pages:
            with self.subTest(available_pages=available_pages):
                response = self.authorized_author_client.get(pages)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_author_user_redirects(self):
        """
        Проверека переадресации при редактировании поста пользователем,
        не являющимся автором.
        """
        page = reverse('posts:post_edit',
                       kwargs={'post_id': PostURLTests.post.id})
        response = self.authorized_client.get(page)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostURLTests.post.id}
        ))

    def test_templates_for_guest_clients(self):
        """
        Проверка доступности templates для неавторизованных пользовтелей.
        """
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': PostURLTests.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostURLTests.user}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostURLTests.post.id}
                    ): 'posts/post_detail.html',
        }
        for address, template in templates_pages_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_templates_for_authorized_author_clients(self):
        """
        Проверка доступности templates для автора.
        """
        templates_pages_names = {
            reverse('posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.id}
                    ): 'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        for address, template in templates_pages_names.items():
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)
