from django.urls import path

from careplans import views


urlpatterns = [
    path("", views.index, name="index"),
    path("api/care-plans/", views.create_care_plan, name="create_care_plan"),
    path("api/care-plans/<str:care_plan_id>/", views.get_care_plan, name="get_care_plan"),
]
