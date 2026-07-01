from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("users_api/user", views.UserViewSet, basename="user")
router.register("users_api/user_permissions", views.UserPermissionViewSet, basename="user_permissions")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", views.LoginApi.as_view()),
    path("check-login/", views.check_login, name="check_login"),
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
    path('my-coachees/link/', views.link_coachee, name='link_coachee'),
    path('my-coachees/update/', views.update_my_coachee, name='update_my_coachee'),
    path('my-coachees/', views.list_my_coachees, name='list_my_coachees'),
    path('coaches/', views.list_coaches, name='list_coaches'),
    path('my-coach/', views.my_coach, name='my_coach'),
    path('admin/dashboard-stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
    path('admin/coaches/', views.admin_coaches, name='admin_coaches'),
    path('admin/coachees/', views.admin_create_coachee, name='admin_create_coachee'),
    path('admin/coaches/<int:coach_id>/forms/', views.admin_coach_forms, name='admin_coach_forms'),
    path('admin/coaches/<int:coach_id>/coachees/', views.admin_coach_coachees, name='admin_coach_coachees'),
]
