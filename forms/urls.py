from django.urls import path

from . import views

urlpatterns = [
    path("types/", views.FormTypeListCreateView.as_view(), name="form_type_list"),
    path("types/<int:pk>/", views.FormTypeDetailView.as_view(), name="form_type_detail"),
    path("types/<int:pk>/full/", views.FormTypeFullView.as_view(), name="form_type_full"),
    path("subsections/", views.FormSubsectionListCreateView.as_view(), name="form_subsection_list"),
    path("subsections/<int:pk>/", views.FormSubsectionDetailView.as_view(), name="form_subsection_detail"),
    path("questions/", views.FormQuestionListCreateView.as_view(), name="form_question_list"),
    path("questions/<int:pk>/", views.FormQuestionDetailView.as_view(), name="form_question_detail"),
    path(
        "questions/<int:pk>/new-version/",
        views.FormQuestionNewVersionView.as_view(),
        name="form_question_new_version",
    ),
    path("forms/", views.FormFormListCreateView.as_view(), name="form_form_list"),
    path("forms/<int:pk>/", views.FormFormDetailView.as_view(), name="form_form_detail"),
    path("pages/", views.FormPageListCreateView.as_view(), name="form_page_list"),
    path("pages/<int:pk>/", views.FormPageDetailView.as_view(), name="form_page_detail"),
    path("pages/<int:pk>/publish/", views.FormPagePublishView.as_view(), name="form_page_publish"),
    path("pages/published/<slug:slug>/", views.PublishedPageView.as_view(), name="published_page"),
    path(
        "pages/published/<slug:slug>/submit/",
        views.PublishedPageSubmitView.as_view(),
        name="published_page_submit",
    ),
    path(
        "pages/with-responses/",
        views.FormPageWithResponsesListView.as_view(),
        name="form_page_with_responses",
    ),
    path(
        "pages/<int:page_id>/submissions/",
        views.FormPageSubmissionListView.as_view(),
        name="form_page_submissions",
    ),
    path(
        "submissions/mine/",
        views.MySubmissionsListView.as_view(),
        name="my_submissions",
    ),
    path(
        "submissions/<int:submission_id>/",
        views.FormPageSubmissionDetailView.as_view(),
        name="form_submission_detail",
    ),
]
