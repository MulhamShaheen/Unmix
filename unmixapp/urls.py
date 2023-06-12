from django.contrib import admin
from django.urls import path
import unmixapp.views as views


urlpatterns = [
    path('login', views.sign_in, name='login'),
    path('logout', views.logout, name='logout'),
    path('sign-up', views.sign_up, name='sign_up'),
    path('profile', views.profile, name='profile'),
    # path('main', views.main, name='home'),
    path('', views.main, name='home'),
    path("feedback/<int:track_id>", views.feedback, name='feedback'),
    path("api/login", views.Authorization.as_view(), name='api_authorization'),
    path("api/tracks/<int:id>", views.TracksView.as_view(), name='api_tracks'),
    path("media/download/<track_id>", views.download, name='media_download'),
]
