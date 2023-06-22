from django.urls import path
from .views import *

urlpatterns = [
    path('home/',HomeView.as_view(),name="home"),
    path('login',LoginView.as_view(),name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("callback", CallbackView.as_view(), name="callback"),
    path("response",AnalizerView.as_view(), name='prompt_resp')
]