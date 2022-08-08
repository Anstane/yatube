from random import randint
from urllib import response

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from ..models import Post, Group, Follow
from ..forms import PostForm

User = get_user_model()


class PostViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='auth')
        cls.another_user = User.objects.create(username='random')
        cls.random_user = User.objects.create(username='random_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.another_client = Client()
        self.another_client.force_login(self.another_user)
        self.random_client = Client()
        self.random_client.force_login(self.random_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index(self):
        """Проверка словаря context - index."""
        response = self.client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertIn('page_obj', response.context)
        self.assertEqual(first_object, PostViewTest.post)

    def test_group_post(self):
        """Проверка словаря context - group_posts."""
        response = self.client.get(
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewTest.group.slug}
                    )
        )
        first_object_group = response.context['group']
        first_object_page_obj = response.context['page_obj'][0]
        group_context = [
            'group',
            'page_obj'
        ]
        for content in group_context:
            with self.subTest(group_context=group_context):
                self.assertIn(content, response.context)
                self.assertEqual(first_object_group,
                                 PostViewTest.group)
                self.assertEqual(first_object_page_obj,
                                 PostViewTest.post)

    def test_profile_post(self):
        """Проверка словаря context - profile."""
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewTest.user}
                    )
        )
        first_object_author = response.context['author']
        first_object_page_obj = response.context['page_obj'][0]
        profile_context = [
            'author',
            'page_obj',
        ]
        for content in profile_context:
            with self.subTest(profile_context=profile_context):
                self.assertIn(content, response.context)
                self.assertEqual(first_object_author,
                                 PostViewTest.post.author)
                self.assertEqual(first_object_page_obj, PostViewTest.post)

    def test_detail_post(self):
        """Проверка словаря context - post_detail."""
        response = self.client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostViewTest.post.id}
                    )
        )
        first_object = response.context['post']
        self.assertIn('post', response.context)
        self.assertEqual(first_object, PostViewTest.post)

    def test_create_edit_post_get_correct_context_and_form(self):
        """
        Проверяем корректрость словаря context
        create_post и post_edit.
        """
        context_form = [
            reverse('posts:create_post'),
            reverse('posts:post_edit',
                    kwargs={'post_id': PostViewTest.post.id}
                    )
        ]
        for pages in context_form:
            with self.subTest(pages=pages):
                response = self.authorized_client.get(pages)
                form_object = response.context['form']
                self.assertIn('form', response.context)
                self.assertIsInstance(form_object, PostForm)
                if 'is_edit' in response.context:
                    self.assertEqual(response.context['is_edit'], True)

    def test_post_created_on_the_next_pages(self):
        """
        Проверка появления поста на следующих страницах
        """
        post_created_pages = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PostViewTest.group.slug}
                    ),
            reverse('posts:profile',
                    kwargs={'username': PostViewTest.user}
                    ),
        ]
        for page in post_created_pages:
            with self.subTest(post_created_pages=post_created_pages):
                response = self.authorized_client.get(page)
                first_object = response.context['page_obj'][0]
                self.assertEqual(PostViewTest.post, first_object)

    def test_post_in_the_right_group(self):
        """
        Проверка корректоности группы,
        в которую попадает пост
        """
        group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описания 2',
        )
        post_2 = Post.objects.create(
            text='Тестовый пост 2',
            author=PostViewTest.user,
            group=group_2,
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': group_2.slug})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group, post_2.group)

    def test_cache_correct_working(self):
        """Проверяем корректность работы кеша."""
        test_post = Post.objects.create(
            text='Random text',
            author=PostViewTest.user,
            group=PostViewTest.group
        )
        response1 = self.client.get(reverse('posts:index'))
        first_object = response1.content
        test_post.delete()
        response2 = self.client.get(reverse('posts:index'))
        second_object = response2.content
        cache.clear()
        response3 = self.client.get(reverse('posts:index'))
        third_object = response3.content
        self.assertEqual(first_object, second_object)
        self.assertNotEqual(first_object, third_object)
        self.assertNotEqual(second_object, third_object)

    def test_of_subscription(self):
        """Проверяем функционал подписки."""
        count = Follow.objects.filter(
            user=PostViewTest.user,
            author=PostViewTest.another_user).count()
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewTest.another_user.username})
        )
        last_follow = Follow.objects.latest('id')
        another_count = Follow.objects.filter(
            user=PostViewTest.user,
            author=PostViewTest.another_user).count()
        self.assertEqual(another_count, count + 1)
        self.assertEqual(last_follow.user, PostViewTest.user)
        self.assertEqual(last_follow.author, PostViewTest.another_user)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostViewTest.another_user})
        )

    def test_of_unsubscription(self):
        """Проверяем функционал отписки."""
        count = Follow.objects.count()
        Follow.objects.create(
            user = PostViewTest.user,
            author = PostViewTest.another_user,
        )
        another_count = Follow.objects.count()
        self.assertEqual(another_count, count + 1)
        response_2 = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostViewTest.another_user.username})
        )
        one_more_count = Follow.objects.count()
        self.assertEqual(count, one_more_count)
        self.assertRedirects(response_2, reverse(
            'posts:profile',
            kwargs={'username': PostViewTest.another_user})
        )

    def test_user_can_not_sub_on_himself(self):
        """
        Проверяем, может ли пользователь подписаться сам не себя.
        """
        count = Follow.objects.count()
        self.another_client.post(reverse(
            'posts:profile_follow',
            kwargs={
                'username':
                PostViewTest.another_user.username}),
            follow=True,
        )
        another_count = Follow.objects.count()
        self.assertEqual(count, another_count)

    def test_new_post_of_sub_auth_appear(self):
        """
        Проверяем, появляются ли записи авторов,
        у подписанных пользователей.
        """
        PostViewTest.some_user = User.objects.create(username='some_user')
        PostViewTest.some_client = Client()
        PostViewTest.some_client.force_login(PostViewTest.some_user)
        some_post = Post.objects.create(
            text = 'random',
            author = PostViewTest.some_user,
            group = PostViewTest.group
        )
        Follow.objects.create(
            user = PostViewTest.user,
            author = PostViewTest.some_user,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        objects = response.context['page_obj']
        post = Post.objects.first()
        self.assertIn(some_post, objects)
        self.assertEqual(post.text, some_post.text)
        self.assertEqual(post.author, some_post.author)
        self.assertEqual(post.group, some_post.group)

    def test_new_post_of_auth_do_not_appear_for_random(self):
        """
        Проверяем, появляется ли пост у случайных пользоваталей.
        """
        PostViewTest.some_user = User.objects.create(username='some_user')
        PostViewTest.some_client = Client()
        PostViewTest.some_client.force_login(PostViewTest.some_user)
        some_post = Post.objects.create(
            text = 'random',
            author = PostViewTest.some_user,
            group = PostViewTest.group
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        objects = response.context['page_obj']
        self.assertNotIn(some_post, objects)


class PaginatorViewTest(TestCase):
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
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def test_paginator(self):
        """Тестируем корректность работы пагинатора."""
        posts_on_first_page = settings.AMOUNT_OF_POSTS
        posts_on_second_page = randint(1, settings.AMOUNT_OF_POSTS)
        [Post.objects.create(
            text='Тестовый пост',
            author=PaginatorViewTest.user,
            group=PaginatorViewTest.group
        )
            for _ in range(settings.AMOUNT_OF_POSTS + posts_on_second_page - 1)
        ]
        first_page = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': PaginatorViewTest.group.slug}
                    ),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewTest.user}
                    ),
        ]
        for page in first_page:
            with self.subTest(first_page=first_page):
                response1 = self.client.get(page + '?page=1')
                response2 = self.client.get(page + '?page=2')
                self.assertEqual(len(response1.context['page_obj']),
                                 posts_on_first_page)
                self.assertEqual(len(response2.context['page_obj']),
                                 posts_on_second_page)
