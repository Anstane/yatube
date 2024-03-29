from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_post, name='create_post'),
    path('posts/<post_id>/edit/', views.post_edit, name='post_edit'),
    path('profile/<username>/', views.profile, name='profile'),
    path('posts/<post_id>/', views.post_detail, name='post_detail'),
    path('group/<slug:slug>/', views.group_posts, name='group_posts'),
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
    path('follow/', views.follow_index, name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
