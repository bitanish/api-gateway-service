from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from .views import test_protect

urlpatterns = [
    path('api/token',TokenObtainPairView.as_view()),
    path('api/refresh',TokenRefreshView.as_view()),
    path('api/test',test_protect)
]