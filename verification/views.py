from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . import models

                
@login_required
def index(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    return render(request, 'verification/index.html', {'page_title': 'Home', 'u_data': user_access, 'ex_user': ex_user})

@login_required
def find_vitem(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    if request.POST:
        if request.POST['person']:
            result = models.VerificationItem.objects.filter(person__person__fio__icontains = request.POST['person'].upper())
        else:
            result = models.VerificationItem.objects.filter(organization__organization__full_name__icontains = request.POST['organization'].upper())
        if request.user.extendeduser.user_role.role_lvl > 3:
            result = result.filter(author__user_role = request.user.extendeduser.user_role)
    return render(request, 'verification/forms/find_item_result.html', {'page_title': 'Поиск заявок', 'u_data': user_access, 'ex_user': ex_user, 'result': result})

@login_required
def create_item(request):
    user_access = [models.ExtendedUser.objects.get(id=request.user.id).user_role.role_name, models.ExtendedUser.objects.get(id=request.user.id).access_lvl]
    ex_user = models.ExtendedUser.objects.get(user=request.user)
    if request.method == 'GET':
        
        return render(request, 'verification/create_item.html', {'page_title': 'Создание заявки', 'ex_user': ex_user})

    elif request.POST['item_type'] == 'Агент':        
        
        return redirect('create-agent')

    elif request.POST['item_type'] == 'Партнер':

        return redirect('create-partner')

    elif request.POST['item_type'] == 'Штатный сотрудник':
        
        return redirect('create-staff')

    elif request.POST['item_type'] == 'Контрагент':
        
        return redirect('create-counterparty')