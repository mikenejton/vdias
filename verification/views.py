from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse
from djqscsv import render_to_csv_response
from . import models, forms, views_utils


                
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
            if request.POST['person']:
                result = result.filter(Q(person__person__fio__icontains = request.POST['person'].upper()) | Q(person__person__sneals = request.POST['person']))
            elif request.POST['organization']:
                result = result.filter(Q(organization__organization__full_name__icontains = request.POST['organization'].upper()) | Q(organization__organization__inn = request.POST['organization']) | Q(organization__organization__ogrn = request.POST['organization']) )
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
def create_item(request):
    context = views_utils.get_base_context(request.user)
    if request.method == 'GET':
        context['page_title'] = 'Создание заявки'
        context['create_stage'] = 'type_choice'
        template = 'verification/create_item.html'
    elif request.POST['create_stage'] == 'type_choice':
        if request.POST['item_type'] == 'Короткая заявка':
            return redirect('create-short-item')

        context['page_title'] = 'Поиск совпадений'
        context['item_type'] = request.POST['item_type']
        context['create_stage'] = 'item_search'
        template = 'verification/search_item.html'
    elif request.POST['create_stage'] == 'item_search':
        if request.POST['item_type'] in ('Партнер', 'Контрагент'):
            if 'inn' in request.POST:
                found = models.OrganizationWithRole.objects.filter(organization__inn = request.POST['inn'])
            elif 'ogrn' in request.POST:
                found = models.OrganizationWithRole.objects.filter(organization__ogrn = request.POST['ogrn'])
            if len(found):
                is_twin = False
                for owr in found:
                    if owr.role == request.POST['item_type']:
                        vitem = models.VerificationItem.objects.filter(organization = owr)
                        return redirect(reverse('vitem', args=[vitem[0].id]))
                
                vitem = models.VerificationItem.objects.filter(organization = found[0])
                owr = models.OrganizationWithRole()
                owr.organization = found[0].organization
                owr.role = models.ObjectRole.objects.get(role_name=request.POST['item_type'])
                if request.POST['item_type'] == 'Партнер':
                    owr.organization_type = request.user.extendeduser.user_role.role_name
                else:
                    owr.organization_type = request.POST['item_type']
                owr.author = request.user.extendeduser
                owr.save()
                org_admins = models.PersonWithRole.objects.filter(related_organization = found[0], role__role_name__in = ['Бенефициар', 'Ген. директор'])
                if len(org_admins):
                    for org_admin in org_admins:
                        new_admin = models.PersonWithRole()
                        new_admin.person = org_admin.person
                        new_admin.related_organization = owr
                        new_admin.role = org_admin.role
                        new_admin.verificated = org_admin.verificated
                        new_admin.author = request.user.extendeduser
                        new_admin.save()
                is_shadow = len(vitem) > 0
                vitem_id = views_utils.vitem_creator(request, owr, 'organization', is_shadow, vitem)
                return redirect(reverse('vitem', args=[vitem_id]))
            elif request.POST['item_type'] == 'Партнер':
                return redirect('create-partner')
            elif request.POST['item_type'] == 'Контрагент':
                return redirect('create-counterparty')

        elif request.POST['item_type'] in ('Агент', 'Штатный сотрудник'):
            found = models.PersonWithRole.objects.filter(person__sneals = request.POST['sneals'])
            if len(found):
                vitem = models.VerificationItem.objects.filter(person = found[0], is_shadow = False)
                if found[0].role == request.POST['item_type']:
                    return redirect(reverse('vitem', args=[vitem[0].id]))
                else:
                    pwr = models.PersonWithRole()
                    pwr.person = found[0].person
                    pwr.role = request.POST['item_type']
                    pwr.related_organization = found[0].related_organization
                    pwr.related_manager = found[0].related_manager
                    pwr.author = request.user.extendeduser
                    pwr.save()
                    vitem_id = views_utils.vitem_creator(request, pwr, 'person', len(vitem), vitem)
                    return redirect(reverse('vitem', args=[vitem_id]))

            elif request.POST['item_type'] == 'Агент':
                return redirect('create-agent')
            elif request.POST['item_type'] == 'Штатный сотрудник':
                return redirect('create-staff')
    
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
        template = 'verification/forms/testforms/new_item_type_selection.html'
        return render(request, template, context)
    else:
        return redirect(reverse('item-searcher', args=[request.POST['item_type']]))

@login_required
def item_searcher(request, item_type = None, owr_id = None):
    context = views_utils.get_base_context(request.user)
    if request.method == 'GET':
        if item_type == 'short-item':
            return redirect('create-short-item')

        template = 'verification/forms/testforms/search_item.html'
        context['page_title'] = 'Поиск совпадений'
        context['item_type'] = item_type
        context['owr_id'] = owr_id if owr_id else 0
        
        return render(request, template, context)
    
    elif request.method == 'POST':
        
        return render(request, template, context)





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