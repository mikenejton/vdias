from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from . import models, forms, utils


                
@login_required
def index(request):
    context = utils.get_base_context(request.user)
    context['page_title'] = 'Верификация'
    return render(request, 'verification/index.html', context)

@login_required
def find_vitem(request):
    context = utils.get_base_context(request.user)
    if request.POST:
        if request.POST['person']:
            result = models.VerificationItem.objects.filter(person__person__fio__icontains = request.POST['person'].upper())
        else:
            result = models.VerificationItem.objects.filter(organization__organization__full_name__icontains = request.POST['organization'].upper())
        if request.user.extendeduser.user_role.role_lvl > 3:
            result = result.filter(author__user_role = request.user.extendeduser.user_role)
        elif request.user.extendeduser.user_role.role_lvl == 3:
            result = result.exclude(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент'))
        context['result'] = result
    context['page_title'] = 'Поиск заявки'
    return render(request, 'verification/forms/vitem_search_result.html', context)

def vitem_list(request, param=None):
    context = utils.get_base_context(request.user)
    context['page_title'] = 'Список заявок'
    result = context['stats'].q_all
    if request.POST:
        if request.POST['person']:
            result = result.filter(person__person__fio__icontains = request.POST['person'].upper())
        if request.POST['organization']:
            result = result.filter(organization__organization__full_name__icontains = request.POST['organization'].upper())
    elif param:
        result = getattr(context['stats'], param)
    
    if request.user.extendeduser.user_role.role_lvl > 3:
        result = result.filter(author__user_role = request.user.extendeduser.user_role)
    elif request.user.extendeduser.user_role.role_lvl == 3:
        result = result.exclude(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент'))
    
    context['result'] = result
    return render(request, 'verification/forms/vitem_search_result.html', context)

@login_required
def create_item(request):
    if request.method == 'GET':
        context = utils.get_base_context(request.user)
        context['page_title'] = 'Создание заявки'
        return render(request, 'verification/create_item.html', context)

    elif request.POST['item_type'] == 'Агент':        
        return redirect('create-agent')

    elif request.POST['item_type'] == 'Партнер':
        return redirect('create-partner')

    elif request.POST['item_type'] == 'Штатный сотрудник':
        return redirect('create-staff')

    elif request.POST['item_type'] == 'Контрагент':
        return redirect('create-counterparty')

    
def scan_upload(request):
    if request.FILES:
        form = forms.DocStorageForm(request.POST, request.FILES)
        if form.is_valid():
            new_scan = form.save()
            required_scan_checking(new_scan)
    return redirect(request.META.get('HTTP_REFERER'))


def scan_delete(request, scan_id=None):
    current_scan = models.DocStorage.objects.get(id=scan_id)
    current_scan.to_del = True
    current_scan.save()
    required_scan_checking(current_scan)
    return redirect(request.META.get('HTTP_REFERER'))

def required_scan_checking(scan):
    
        scan_list = models.DocStorage.objects.filter(model_name = scan.model_name, model_id = scan.model_id).exclude(to_del = True)
        if scan.model_name == 'PersonWithRole':
            vitem = models.VerificationItem.objects.filter(person__id = scan.model_id)[0]
            doc_types = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета']
        elif scan.model_name == 'OrganizationWithRole':
            vitem = models.VerificationItem.objects.filter(organization__id = scan.model_id)[0]
            doc_types = ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет']
        vitem_is_filled = True
        dias_status = 'Новая'
        for doc_type in doc_types:
            if scan_list.filter(doc_type = doc_type).count() == 0:
                vitem_is_filled = False
                dias_status = ''
        vitem.is_filled = vitem_is_filled
        if vitem.dias_status == 'Новая' or vitem.dias_status == '':
            vitem.dias_status = dias_status
        vitem.save()