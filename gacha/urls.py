from django.urls import path
from . import views

app_name = "gacha"

urlpatterns = [
    path("", views.home, name="home"),
    path("g/create/", views.gacha_create, name="create"),
    path("g/<str:public_id>/manage/", views.manage, name="manage"),
    path("g/<str:public_id>/", views.public_view, name="public"),
    path("g/<str:public_id>/draw/", views.draw, name="draw"),
    path("g/<str:public_id>/delete/", views.delete_gacha, name="delete"),

]
