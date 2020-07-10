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
            # Единая строка поиска по трем типам объектов
            # result.filter(Q(person__person__fio__icontains = request.POST['search_str'].upper()) | Q(person__person__sneals = request.POST['search_str']) | Q(organization__organization__full_name__icontains = request.POST['search_str'].upper()) | Q(organization__organization__inn = request.POST['search_str']) | Q(organization__organization__ogrn = request.POST['search_str']) | Q(short_item__item_id__icontains = request.POST['search_str'].upper().strip()))
            if request.POST['person']:
                result = result.filter(Q(person__person__fio__icontains = request.POST['person'].upper()) | Q(person__person__sneals = request.POST['person']))
            elif request.POST['organization']:
                result = result.filter(Q(organization__organization__full_name__icontains = request.POST['organization'].upper()) | Q(organization__organization__inn = request.POST['organization']) | Q(organization__organization__ogrn = request.POST['organization']))
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
    return redirect({request.META.get('HTTP_REFERER')})

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

        twins = views_utils.twin_detecter('Organization' if item_type in ['counterparty', 'partner'] else 'Person', request.POST['inn' if item_type in ['counterparty', 'partner'] else 'sneals'], item_type)
        if not len(twins):
            if owr_id > 0:
                return redirect(reverse(f'create-{item_type}', args=[owr_id]))
            return redirect(reverse(f'create-{item_type}'))
        elif twins[0] == 'new':
            new_item_wr = views_utils.object_wr_creater(request, twins[1]._meta.model.__name__.replace('WithRole', ''), twins[1], models.ObjectRole.objects.get(role = item_type))
            related_vitems_qs = models.VerificationItem.objects.filter(**{f"{twins[1]._meta.model.__name__.replace('WithRole', '').lower()}__{twins[1]._meta.model.__name__.replace('WithRole', '').lower()}__id": twins[1].id})
            is_shadow = len(related_vitems_qs.exclude(**{f"{twins[1]._meta.model.__name__.replace('WithRole', '').lower()}__role__role_name__in": ['Ген. директор', 'Бенефициар']})) > 0
            views_utils.vitem_creator(request, new_item_wr, twins[1]._meta.model.__name__.replace('WithRole', '').lower(), is_shadow=is_shadow, related_vitem=related_vitems_qs)
            return redirect(reverse(f'detailing-{item_type}', args=[new_item_wr.id, owr_id] if owr_id>0 else [new_item_wr.id]))
        elif twins[0] == 'old':
            vitem = models.VerificationItem.objects.filter(**{twins[1]._meta.model.__name__.replace('WithRole', '').lower(): twins[1]})
            return redirect(reverse('vitem', args=[vitem[0].id]))
            





    # elif request.POST['create_stage'] == 'type_choice':
    #     if request.POST['item_type'] == 'Короткая заявка':
    #         return redirect('create-short-item')

    #     context['page_title'] = 'Поиск совпадений'
    #     context['item_type'] = request.POST['item_type']
    #     context['create_stage'] = 'item_search'
    #     template = 'verification/search_item.html'
    # elif request.POST['create_stage'] == 'item_search':
    #     if request.POST['item_type'] in ('Партнер', 'Контрагент'):
    #         if 'inn' in request.POST:
    #             found = models.OrganizationWithRole.objects.filter(organization__inn = request.POST['inn'])
    #         elif 'ogrn' in request.POST:
    #             found = models.OrganizationWithRole.objects.filter(organization__ogrn = request.POST['ogrn'])
    #         if len(found):
    #             is_twin = False
    #             for owr in found:
    #                 if owr.role == request.POST['item_type']:
    #                     vitem = models.VerificationItem.objects.filter(organization = owr)
    #                     return redirect(reverse('vitem', args=[vitem[0].id]))
                
    #             vitem = models.VerificationItem.objects.filter(organization = found[0])
    #             owr = models.OrganizationWithRole()
    #             owr.organization = found[0].organization
    #             owr.role = request.POST['item_type']
    #             if request.POST['item_type'] == 'Партнер':
    #                 owr.organization_type = request.user.extendeduser.user_role.role_name
    #             else:
    #                 owr.organization_type = request.POST['item_type']
    #             owr.author = request.user.extendeduser
    #             owr.save()
    #             org_admins = models.PersonWithRole.objects.filter(related_organization = found[0], role__in = ['Бенефициар', 'Ген. директор'])
    #             if len(org_admins):
    #                 for org_admin in org_admins:
    #                     new_admin = models.PersonWithRole()
    #                     new_admin.person = org_admin.person
    #                     new_admin.related_organization = owr
    #                     new_admin.role = org_admin.role
    #                     new_admin.verificated = org_admin.verificated
    #                     new_admin.author = request.user.extendeduser
    #                     new_admin.save()
    #             is_shadow = len(vitem) > 0
    #             vitem_id = views_utils.vitem_creator(request, owr, 'organization', is_shadow, vitem)
    #             return redirect(reverse('vitem', args=[vitem_id]))
    #         elif request.POST['item_type'] == 'Партнер':
    #             return redirect('create-partner')
    #         elif request.POST['item_type'] == 'Контрагент':
    #             return redirect('create-counterparty')

    #     elif request.POST['item_type'] in ('Агент', 'Штатный сотрудник'):
    #         found = models.PersonWithRole.objects.filter(person__sneals = request.POST['sneals'])
    #         if len(found):
    #             vitem = models.VerificationItem.objects.filter(person = found[0], is_shadow = False)
    #             if found[0].role == request.POST['item_type']:
    #                 return redirect(reverse('vitem', args=[vitem[0].id]))
    #             else:
    #                 pwr = models.PersonWithRole()
    #                 pwr.person = found[0].person
    #                 pwr.role = request.POST['item_type']
    #                 pwr.related_organization = found[0].related_organization
    #                 pwr.related_manager = found[0].related_manager
    #                 pwr.author = request.user.extendeduser
    #                 pwr.save()
    #                 vitem_id = views_utils.vitem_creator(request, pwr, 'person', len(vitem), vitem)
    #                 return redirect(reverse('vitem', args=[vitem_id]))

    #         elif request.POST['item_type'] == 'Агент':
    #             return redirect('create-agent')
    #         elif request.POST['item_type'] == 'Штатный сотрудник':
    #             return redirect('create-staff')
    
    # return render(request, template, context)