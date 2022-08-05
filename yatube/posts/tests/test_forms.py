import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='auth')
        cls.new_user = User.objects.create(username='random_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Случайный комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.new_user)

    def test_create_post_works_correctly(self):
        """
        Проверка на корректность создания постов
        авторизованны пользователем.
        """
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group.pk,
            'image': uploaded
        }
        response = self.authorized_author_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, PostCreateFormTests.user)
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.image, f'posts/{uploaded}')
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user}
        ))

    def test_post_edit_works_correctly(self):
        """
        Проверка на корректоность получемой формы
        при редактировании постов.
        Проверка на появление новых записей в БД.
        """
        test_group = Group.objects.create(
            title='Группа для тестов',
            slug='testing-slug',
            description='Пустое описание'
        )
        test_post = Post.objects.create(
            text='Ещё один тестовый пост',
            author=PostCreateFormTests.user,
            group=PostCreateFormTests.group
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': test_group.pk
        }
        response = self.authorized_author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': test_post.id}
            ),
            data=form_data,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(test_post.text, form_data['text'])
        self.assertEqual(test_post.author, PostCreateFormTests.user)
        self.assertEqual(test_post.group, test_group)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': test_post.id}
        ))

    def test_guest_user_can_not_create_post(self):
        """
        Проверяем не создалось ли новых постов,
        проверяем переадресацию неавторизованного пользователя.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': PostCreateFormTests.group.pk
        }
        response = self.client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        url = reverse('posts:create_post')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_authorized_client_can_not_edit_author_posts(self):
        """
        Проверяем не может ли авторизованный пользователь
        редактировать посты другого автора.
        """
        new_test_group = Group.objects.create(
            title='Группппа для тесстов',
            slug='testing-slugg',
            description='Пустое описание'
        )
        new_test_post = Post.objects.create(
            text='Тесccтоый поссcт',
            author=PostCreateFormTests.user,
            group=new_test_group
        )
        form_data = {
            'text': 'Новый тестовый пост',
            'group': PostCreateFormTests.group.pk
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': new_test_post.id}
            ),
            data=form_data,
            follow=True
        )
        new_test_post.refresh_from_db()
        self.assertNotEqual(new_test_post.text, form_data['text'])
        self.assertNotEqual(new_test_post.author,
                            PostCreateFormTests.new_user)
        self.assertNotEqual(new_test_post.group,
                            PostCreateFormTests.group)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': new_test_post.id}
        ))

    def test_comments_appear_on_page(self):
        """Проверяем появляется ли комментарий после отправки."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Самый последний комментарий'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_user_can_not_create_comment(self):
        """
        Проверяем не может ли неавторизованный пользователь
        создать комментарий.
        """
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Самый новый комментарий'
        }
        response = self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        post_det = reverse('posts:add_comment',
                           kwargs={'post_id': PostCreateFormTests.post.id})
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, f'{login_url}?next={post_det}')
