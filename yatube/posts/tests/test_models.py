from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описания',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_verbose_name(self):
        """Проверка verbose_name полей."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """Проверка help_text полей."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_models_have_str_method(self):
        """Проверка для моделей Post и Group - __str__."""
        testing_str_method = [
            PostModelTest.post.__str__(),
            PostModelTest.group.__str__(),
        ]
        for expected_object_name in testing_str_method:
            with self.subTest(expected_object_name=expected_object_name):
                self.assertIsInstance(expected_object_name, str)

    def test_correct_len(self):
        """
        Проверка на количество символов
        передаваемое в метод __str__ модели Post.
        """
        max_length = settings.SYMBOLS_IN_STR
        str_method = PostModelTest.post.__str__()
        length_post = len(str_method)
        self.assertTrue(length_post <= max_length)

    def test_str_method_correct_fields(self):
        """Проверка отображаемых полей метода __str__."""
        str_method = {
            PostModelTest.post.__str__():
            PostModelTest.post.text[:settings.SYMBOLS_IN_STR],
            PostModelTest.group.__str__():
            PostModelTest.group.title,
        }
        for str_field, field in str_method.items():
            with self.subTest(str_field=str_field):
                self.assertEqual(str_field, field)
