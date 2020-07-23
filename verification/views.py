from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse
from djqscsv import render_to_csv_response
from . import models, forms, views_utils, views_sub_func


                
@login_required
def index(request):
    context = views_utils.get_base_context(request.user)
    context['page_title'] = 'ДИАС'
    if request.user.extendeduser.user_role.role_lvl <= 2:
        context['chat_messages'] = models.VitemChat.objects.exclude(author = request.user.extendeduser).order_by('-created')[:20]
    else:
        context['chat_messages'] = models.VitemChat.objects.filter(Q(vitem__author = request.user.extendeduser) | Q(vitem__case_officer = request.user.extendeduser)).exclude(author = request.user.extendeduser).order_by('-created')[:20]

    return render(request, 'verification/index.html', context)

@login_required
def vitem_list(request, param=None):
    context = views_utils.get_base_context(request.user)
    context['page_title'] = 'Список заявок'
    result = context['stats'].q_all
    template = 'verification/forms/vitem_search_result.html'
    if request.POST:
        if not param:
            result = result.filter(Q(person__person__fio__icontains = request.POST['search_str'].upper()) | Q(person__person__sneals = request.POST['search_str']) | Q(organization__organization__full_name__icontains = request.POST['search_str'].upper()) | Q(organization__organization__inn = request.POST['search_str']) | Q(organization__organization__ogrn = request.POST['search_str']) | Q(short_item__item_id__icontains = request.POST['search_str'].upper().strip()))
    elif param:
        result = getattr(context['stats'], param)
        context['q_name'] = param
    if len(result):
        if request.user.extendeduser.user_role.role_lvl > 3:
            result = result.filter(author__user_role = request.user.extendeduser.user_role)
        elif request.user.extendeduser.user_role.role_lvl == 3:
            result = result.exclude(Q(person__role = 'Сотрудник') | Q(organization__role = 'Контрагент'))
    if len(result) == 0:
        context['err_txt'] = 'Результаты не найдены'
        template = 'verification/404.html'
    context['result'] = result
    return render(request, template, context)

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

@login_required
def new_item_type_selection(request):
    context = views_utils.get_base_context(request.user)
    if request.method == 'GET':
        context['page_title'] = 'Тип объекта'
        template = 'verification/forms/new_item_type_selection.html'
        return render(request, template, context)
    else:
        return redirect(reverse('item-searcher', args=[request.POST['item_type'], 0]))

@login_required
def item_searcher(request, item_type = None, owr_id = 0):
    context = views_utils.get_base_context(request.user)
    if request.method == 'GET':
        if item_type == 'short-item':
            return redirect('create-short-item')

        template = 'verification/forms/search_item.html'
        context['page_title'] = 'Поиск совпадений'
        context['item_type'] = item_type
        context['owr_id'] = owr_id if owr_id else 0
        return render(request, template, context)
    
    elif request.method == 'POST':
        if 'cancel' in request.POST:
            if owr_id > 0:
                return redirect(reverse(f'create-{item_type}', args=[owr_id]))

            return redirect(reverse(f'create-{item_type}'))
        org_id = None
        if owr_id != 0:
            org = models.OrganizationWithRole.objects.get(id = owr_id)
            if org:
                org_id = org.organization.id
        twins = views_utils.twin_detecter('Organization' if item_type in ['counterparty', 'partner'] else 'Person', request.POST['inn' if item_type in ['counterparty', 'partner'] else 'sneals'], item_type)
        if not len(twins):
            if owr_id > 0:
                return redirect(reverse(f'create-{item_type}', args=[owr_id]))
            return redirect(reverse(f'create-{item_type}'))
        elif twins[0] == 'new':
            new_item_wr = views_utils.object_wr_creater(request, twins[1]._meta.model.__name__.replace('WithRole', ''), twins[1], models.ObjectRole.objects.get(role = item_type), org_id)
            related_vitems_qs = models.VerificationItem.objects.filter(**{f"{twins[1]._meta.model.__name__.replace('WithRole', '').lower()}__{twins[1]._meta.model.__name__.replace('WithRole', '').lower()}__id": twins[1].id})
            is_shadow = len(related_vitems_qs.exclude(**{f"{twins[1]._meta.model.__name__.replace('WithRole', '').lower()}__role__role_name__in": ['Ген. директор', 'Бенефициар']})) > 0
            if new_item_wr.role.role_name != 'Бенефициар':
                views_utils.vitem_creator(request, new_item_wr, twins[1]._meta.model.__name__.replace('WithRole', '').lower(), is_shadow=is_shadow, related_vitem=related_vitems_qs)
                return redirect(reverse(f'detailing-{item_type}', args=[owr_id, new_item_wr.id] if owr_id>0 else [new_item_wr.id]))
            else:
                return redirect(reverse(f'detailing-{item_type}', args=[owr_id, new_item_wr.id] if owr_id>0 else [new_item_wr.id]))
        elif twins[0] == 'old':
            vitem = models.VerificationItem.objects.filter(**{twins[1]._meta.model.__name__.replace('WithRole', '').lower(): twins[1]})
            return redirect(reverse('vitem', args=[vitem[0].id]))