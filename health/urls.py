from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("learn/", views.learning_hub, name="learning_hub"),
    path("account/profile/", views.account_profile, name="account_profile"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("cycles/", views.cycle_calendar, name="cycle_calendar"),
    path("reports/", views.health_report, name="health_report"),
    path("ultrasound/", views.ultrasound_intake, name="ultrasound_intake"),
    path("ultrasound/<int:image_id>/image/", views.view_ultrasound_image, name="view_ultrasound_image"),
    path("ultrasound/<int:image_id>/preview/", views.preprocess_ultrasound_image, name="preprocess_ultrasound_image"),
    path("ultrasound/<int:image_id>/delete/", views.delete_ultrasound_image, name="delete_ultrasound_image"),
    path("records/<str:entry_type>/<int:entry_id>/edit/", views.edit_entry, name="edit_entry"),
    path("records/<str:entry_type>/<int:entry_id>/delete/", views.delete_entry, name="delete_entry"),
    path("account/delete/", views.delete_account, name="delete_account"),
]
