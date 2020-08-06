from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Count, Max
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

def export_csv(request):
    if request.method == 'POST':
        if 'report_name' in request.POST:
            if request.POST['report_name'] == 'organizations':
                q = models.Organization.objects.annotate(
                    agents_count=Count("personwithrole", filter=~Q(personwithrole__role__role_name__in = ['Ген. директор', 'Бенефициар', 'Сотрудник']))
                ).annotate(
                    ceo=Max('personwithrole__person__fio', filter=Q(personwithrole__role__role_name = 'Ген. директор'))
                ).prefetch_related('owr', 'owr__vitem_owr')
                fieldset = ['id', 'owr__role__role_name', 'org_form', 'org_name', 'agents_count', 'inn', 'ogrn', 'ceo', 'adr_reg', 'owr__division__division_name', 'owr__product_type__product_type', 'owr__partnership_status__status', 'comment', 'media_folder', 'created', 'owr__vitem_owr__created', 'owr__vitem_owr__status__status', 'owr__vitem_owr__dias_comment', 'owr__vitem_owr__case_officer__user__last_name', 'author__user__last_name', 'owr__vitem_owr__fms_not_ok', 'owr__vitem_owr__docs_full', 'owr__vitem_owr__reg_checked', 'owr__vitem_owr__rosfin', 'owr__vitem_owr__cronos', 'owr__vitem_owr__cronos_status', 'owr__vitem_owr__fssp', 'owr__vitem_owr__fssp_status', 'owr__vitem_owr__bankruptcy', 'owr__vitem_owr__bankruptcy_status', 'owr__vitem_owr__court', 'owr__vitem_owr__court_status', 'owr__vitem_owr__contur_focus', 'owr__vitem_owr__contur_focus_status', 'owr__vitem_owr__affiliation', 'owr__vitem_owr__affiliation_status', 'owr__vitem_owr__soc', 'owr__vitem_owr__soc_status']
            
            elif request.POST['report_name'] == 'persons':
                q = models.Person.objects.annotate(
                    roles_count=Count("pwr")
                ).prefetch_related('pwr', 'pwr__vitem_pwr')
                
                fieldset = ['id', 'pwr__role__role_name', 'roles_count', 'sneals', 'fio', 'pwr__related_organization__full_name', 'staff_dep__dep_name', 'staff_position', 'owr__staff_status', 'city', 'dob', 'phone_number', 'pwr__related_manager__division__division_name', 'pwr__product_type__product_type', 'pwr__partnership_status__status', 'comment', 'media_folder', 'video_upload_date', 'video_check_date', 'created', 'author__user__last_name', 'pwr__vitem_pwr__status__status', 'pwr__vitem_pwr__dias_comment', 'pwr__vitem_pwr__case_officer__user__last_name', 'pwr__vitem_pwr__created', 'pwr__vitem_pwr__fms_not_ok', 'pwr__vitem_pwr__docs_full', 'pwr__vitem_pwr__reg_checked', 'pwr__vitem_pwr__rosfin', 'pwr__vitem_pwr__cronos', 'pwr__vitem_pwr__cronos_status', 'pwr__vitem_pwr__fssp', 'pwr__vitem_pwr__fssp_status', 'pwr__vitem_pwr__bankruptcy', 'pwr__vitem_pwr__bankruptcy_status', 'pwr__vitem_pwr__court', 'pwr__vitem_pwr__court_status', 'pwr__vitem_pwr__contur_focus', 'pwr__vitem_pwr__contur_focus_status', 'pwr__vitem_pwr__affiliation', 'pwr__vitem_pwr__affiliation_status', 'pwr__vitem_pwr__soc', 'pwr__vitem_pwr__soc_status']
            elif request.POST['report_name'] == 'vitems':
                q = models.VerificationItem.objects.all()
                fieldset = [
                    'id',
                    'person__person__id',
                    'person__person__fio',
                    'person__person__prev_fio',
                    'person__role__role_name',
                    'person__verificated',
                    'person__related_manager__fio',
                    'person__related_manager__division__division_name',
                    'person__division__division_name',
                    'person__product_type__product_type',
                    'person__partnership_status__status',
                    'person__staff_status',
                    'person__related_organization__full_name',
                    'person__created',
                    'person__author__user__last_name',
                    'person__person__dob',
                    'person__person__pob',
                    'person__person__adr_reg',
                    'person__person__adr_fact',
                    'person__person__city',
                    'person__person__pass_sn',
                    'person__person__pass_date',
                    'person__person__pass_org',
                    'person__person__pass_code',
                    'person__person__sneals',
                    'person__person__phone_number',
                    'person__person__email',
                    'person__person__staff_dep__dep_name',
                    'person__person__staff_position',
                    'person__person__comment',
                    'person__person__media_folder',
                    'person__person__video_upload_date',
                    'person__person__video_check_date',
                    'person__person__created',
                    'person__person__author__user__last_name',
                    'organization__organization__id',
                    'organization__organization__org_form',
                    'organization__organization__org_name',
                    'organization__role__role_name',
                    'organization__division__division_name',
                    'organization__product_type__product_type',
                    'organization__partnership_status__status',
                    'organization__verificated', 'organization__created',
                    'organization__author__user__last_name',
                    'organization__organization__adr_reg',
                    'organization__organization__adr_fact',
                    'organization__organization__inn',
                    'organization__organization__ogrn',
                    'organization__organization__phone_number',
                    'organization__organization__email',
                    'organization__organization__media_folder',
                    'organization__organization__comment',
                    'organization__organization__created',
                    'organization__organization__author__user__last_name',
                    'is_filled',
                    'status__status',
                    'to_fix',
                    'fixed',
                    'dias_comment',
                    'case_officer__user__last_name',
                    'related_vitem', 'is_shadow',
                    'fms_not_ok', 'rosfin',
                    'docs_full',
                    'reg_checked',
                    'cronos_status',
                    'cronos',
                    'fssp_status',
                    'fssp',
                    'bankruptcy_status',
                    'bankruptcy',
                    'court_status',
                    'court',
                    'contur_focus_status',
                    'contur_focus',
                    'affiliation_status',
                    'affiliation',
                    'soc_status',
                    'soc',
                    'edited',
                    'created',
                    'author__user__last_name'
                ]

            qs_to_csv = q.values(*fieldset)
            return render_to_csv_response(qs_to_csv, delimiter=';')
    
        context = views_utils.get_base_context(request.user)
        context['err_txt'] = 'Не указан отчет для выгрузки'
        return render(request, 'verification/404.html', context)

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
    template = 'verification/forms/search_item.html'
    context['page_title'] = 'Поиск совпадений'
    context['item_type'] = item_type
    context['owr_id'] = owr_id if owr_id else 0
    context['form'] = forms.SearchForm()
    if request.method == 'GET':
        if item_type == 'short-item':
            return redirect('create-short-item')
    
    elif request.method == 'POST':
        if 'cancel' in request.POST:
            if owr_id > 0:
                return redirect(reverse(f'create-{item_type}', args=[owr_id]))

            return redirect(reverse(f'create-{item_type}'))
        org_id = None
        context['form'] = forms.SearchForm(data=request.POST)
        if context['form'].is_valid():
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
    
    return render(request, template, context)