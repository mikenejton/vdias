from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from . import models

                
@login_required
def index(request):
    return render(request, 'verification/index.html', {'page_title': 'Home'})

@login_required
def find_vitem(request):
    if request.POST:
        if request.POST['person']:
            result = models.VerificationItem.objects.filter(person__person__fio__icontains = request.POST['person'].upper())
        else:
            result = models.VerificationItem.objects.filter(organization__organization__full_name__icontains = request.POST['organization'].upper())
        if request.user.extendeduser.user_role.role_lvl > 3:
            result = result.filter(author__user_role = request.user.extendeduser.user_role)
    return render(request, 'verification/forms/find_item_result.html', {'page_title': 'Поиск заявок', 'result': result})

@login_required
def create_item(request):
    if request.method == 'GET':
        return render(request, 'verification/create_item.html', {'page_title': 'Создание заявки'})

    elif request.POST['item_type'] == 'Агент':        
        return redirect('create-agent')

    elif request.POST['item_type'] == 'Партнер':
        return redirect('create-partner')

    elif request.POST['item_type'] == 'Штатный сотрудник':
        return redirect('create-staff')

    elif request.POST['item_type'] == 'Контрагент':
        return redirect('create-counterparty')

    
def scan_delete(request, scan_id=None):
    current_scan = models.DocStorage.objects.get(id=scan_id)
    current_scan.to_del = True
    current_scan.save()
    return redirect(request.META.get('HTTP_REFERER'))