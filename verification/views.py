from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from djqscsv import render_to_csv_response
from . import models, forms, views_utils


                
@login_required
def index(request):
    context = views_utils.get_base_context(request.user)
    context['page_title'] = 'ДИАС'
    if request.user.extendeduser.user_role.role_lvl <= 2:
        context['chat_messages'] = models.VitemChat.objects.exclude(author = request.user.extendeduser).order_by('-created')[:5]
    else:
        context['chat_messages'] = models.VitemChat.objects.filter(Q(vitem__author = request.user.extendeduser) | Q(vitem__case_officer = request.user.extendeduser)).exclude(author = request.user.extendeduser).order_by('-created')[:5]

    return render(request, 'verification/index.html', context)

@login_required
def vitem_list(request, param=None):
    context = views_utils.get_base_context(request.user)
    context['page_title'] = 'Список заявок'
    result = context['stats'].q_all
    if request.POST:
        if not param:
            if request.POST['person']:
                result = result.filter(person__person__fio__icontains = request.POST['person'].upper())
            elif request.POST['organization']:
                result = result.filter(organization__organization__full_name__icontains = request.POST['organization'].upper())
            elif request.POST['short_item']:
                result = result.filter(short_item__item_id__icontains = request.POST['short_item'].upper().strip())
            else:
                result = {}
    elif param:
        result = getattr(context['stats'], param)
        context['q_name'] = param
    if len(result):
        if request.user.extendeduser.user_role.role_lvl > 3:
            result = result.filter(author__user_role = request.user.extendeduser.user_role)
        elif request.user.extendeduser.user_role.role_lvl == 3:
            result = result.exclude(Q(person__role = 'Штатный сотрудник') | Q(organization__role = 'Контрагент'))
    
    context['result'] = result    
    return render(request, 'verification/forms/vitem_search_result.html', context)

@login_required
def create_item(request):
    if request.method == 'GET':
        context = views_utils.get_base_context(request.user)
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

    elif request.POST['item_type'] == 'Короткая заявка':
        return redirect('create-short-item')

@login_required    
def scan_upload(request):
    if request.FILES:
        form = forms.DocStorageForm(request.POST, request.FILES)
        if form.is_valid():
            new_scan = form.save()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def scan_delete(request, scan_id=None):
    current_scan = models.DocStorage.objects.get(id=scan_id)
    current_scan.to_del = True
    current_scan.save()
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def sendmail(request):
    views_utils.send_mail('dp@finfort.ru', 'Тема письма', 'Это вроде как от Юли<br>Но не от Юли!')
    return redirect('index')

def export_csv(request, param=None):
    if request.POST:
        qs = 'queryset to save'
        return render_to_csv_response(qs)
    else:
        return redirect(request.META.get('HTTP_REFERER'))