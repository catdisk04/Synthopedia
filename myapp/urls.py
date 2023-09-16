from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"), 
    path("predict/", views.predict, name="predict"), 
    path("optimise/", views.optimise, name="optimise")
]