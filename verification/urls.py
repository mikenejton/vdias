from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('find-vitem', views.find_vitem, name='find-vitem'),
    path('create-item', views.create_item, name='create-item'),
    path('create-item/agent', views.agent_form, name='create-agent')
    
]