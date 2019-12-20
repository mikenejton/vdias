from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('/find-vitem', views.find_vitem, name='find-vitem')
]