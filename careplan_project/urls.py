from django.urls import path

from careplans import views


urlpatterns = [
    path("", views.index, name="index"),
    path("api/care-plans/", views.create_care_plan, name="create_care_plan"),
]
