from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from . import models

# Логирование действий пользователя
def update_logger(model_name, pk, action, username, new_set=False, old_set=''):
    if not new_set:
        new_dl = models.DataLogger()
        new_dl(model_name=model_name, model_id=pk, action='Создание записи', author=username)
    else:
        changes = []
        for i in new_set._meta.get_fields():
            print('OLD {} - NEW {}'.format(getattr(old_set, i.name), getattr(new_set, i.name)))
            if getattr(old_set, i.name) != getattr(new_set, i.name):
                changes.append([i.name, getattr(new_set, i.name), getattr(old_set, i.name)])
        print(changes)
        if len(changes) > 0:
            for i in changes:
                new_dl = models.DataLogger()
                new_dl(model_name=model_name, model_id=pk, action='Обновление записи', field_name=i[0], new_value=i[1], old_value=i[2], author=username)
                
@login_required
def index(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    return render(request, 'verification/index.html', {'page_title': 'Home', 'u_data': user_access, 'ex_user': ex_user})

def find_vitem(request):
    print(request.POST)
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    if request.POST:
        if request.POST['person']:
            result = models.VerificationItem.objects.filter(person__person__fio__icontains = request.POST['person'])
            
        else:
            result = models.VerificationItem.objects.filter(organization__organization__full_name__icontains = request.POST['person'])
        print(result)
    return render(request, 'verification/find_item_result.html', {'page_title': 'Поиск заявок', 'u_data': user_access, 'ex_user': ex_user, 'result': result})

