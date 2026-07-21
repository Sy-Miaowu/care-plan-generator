from django.urls import path

from careplans import views


urlpatterns = [
    path("", views.index, name="index"),
    path("api/care-plans/", views.create_care_plan, name="create_care_plan"),
    path(
        "api/careplan/<str:care_plan_id>/status/",
        views.get_care_plan_status,
        name="get_care_plan_status",
    ),
    path("api/care-plans/<str:care_plan_id>/", views.get_care_plan, name="get_care_plan"),
]
