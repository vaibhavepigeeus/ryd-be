from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("users_api/user", views.UserViewSet, basename="user")
router.register("users_api/user_permissions", views.UserPermissionViewSet, basename="user_permissions")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", views.LoginApi.as_view()),
    path("register/", views.RegisterApi.as_view()),
    path("forgot-password/", views.forgotPassword, name="ResetPassword"),
    path("reset-password/", views.resetPassword, name="resetPassword"),
    path("check-user/", views.checkUser, name="checkUser"),
    path("verify-otp/", views.verifyOTP, name="verifyOTP"),
    path("create-password/", views.createPassword, name="createPassword"),
    path("logout/", views.user_logout, name="logout"),
    path("user-deactivation/", views.deactivateUser, name="deactivateUser"),
    path("user-activation/", views.activateUser, name="activateUser"),
    path("check-password/", views.checkOldPassword, name="checkOldPassword"),
    path(
        "token/refresh/", views.GenerateNewAccessToken.as_view(), name="token_refresh"
    ),
    path(
        "user-data-decryption/",
        views.DecryptUserDataAPIView.as_view(),
        name="decrypt_user_data",
    ),
    path("oauth_login/", views.oauth_login, name="FetchAzureAccessToken"),
    path("check_user_exists_or_not/", views.check_user_exists_or_not, name="check_user_exists_or_not"),
    path('get_users_list/', views.get_users_list, name='get_users_list'),
    path('auth_check/', views.check_auth, name='check_auth'),
    path('my-coachees/', views.list_my_coachees, name='list_my_coachees'),
]
