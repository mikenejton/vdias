from . import models
from django.db.models import Q
from django.core.mail import EmailMessage
class UserStats:
    def __init__(self):
        pass

# Базовый контекст для меню
def get_base_context(user):
    context = {}
    stats = UserStats()
    stats.q_all = models.VerificationItem.objects.all().order_by('-created').select_related()
    stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True)
    stats.q_mine = stats.q_all.filter(case_officer__user = user)
    stats.q_at_work = stats.q_all.filter(dias_status = 'В работе')
    stats.q_to_fix = stats.q_all.filter(to_fix = True)
    stats.q_fixed = stats.q_all.filter(fixed = True)
    stats.q_finished = stats.q_all.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
    stats.q_not_filled = stats.q_all.filter(is_filled = False, dias_status = 'Новая')
    if user.extendeduser.user_role.role_lvl == 2:
        stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True).filter(Q(person__role = 'Штатный сотрудник') | Q(organization__role = 'Контрагент')) #????????? штатник и контрагент?
    if user.extendeduser.user_role.role_lvl == 3:
        stats.q_all = stats.q_all.exclude(Q(person__role = 'Штатный сотрудник') | Q(organization__role = 'Контрагент')).exclude(Q(is_filled = False) & Q(dias_status = 'Новая'))
        stats.q_new = stats.q_all.filter(dias_status = 'Новая')
        stats.q_at_work = stats.q_mine.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_mine.filter(to_fix = True)
        stats.q_fixed = stats.q_mine.filter(fixed = True)
        stats.q_finished = stats.q_mine.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
        stats.q_not_filled = stats.q_mine.filter(is_filled = False, dias_status = 'Новая')
    elif user.extendeduser.user_role.role_lvl >= 4:
        stats.q_all = stats.q_all.filter(author__user_role = user.extendeduser.user_role)
        stats.q_new = stats.q_all.filter(dias_status = 'Новая')
        stats.q_mine = stats.q_all.filter(author__user = user)
        stats.q_at_work = stats.q_mine.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_mine.filter(to_fix = True)
        stats.q_fixed = stats.q_mine.filter(fixed = True)
        stats.q_finished = stats.q_mine.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
        stats.q_not_filled = stats.q_mine.filter(is_filled = False, dias_status = 'Новая')
    context['stats'] = stats
    return context
    
# Логирование действий пользователя
def update_logger(model_name, pk, action, username, new_set=False):
    if not new_set:
        new_dl = models.DataLogger(model_name=model_name, model_id=pk, action='Создание записи', author=username)
        new_dl.save()
    else:
        changes = []
        old_set = getattr(models, model_name).objects.get(id=pk)
        for i in new_set._meta.fields:
            if getattr(old_set, i.name) != getattr(new_set, i.name) and i.name != 'fio':
                changes.append([i.name, getattr(new_set, i.name), getattr(old_set, i.name)])
        if len(changes) > 0:
            for i in changes:
                new_dl = models.DataLogger(model_name=model_name, model_id=pk, action='Обновление записи', field_name=i[0], new_value=i[1], old_value=i[2], author=username)
                new_dl.save()

def vitem_creator(request, item, item_type, is_shadow=False, related_vitem = None):
    vitem = models.VerificationItem.objects.filter(**{item_type: item})
    if not len(vitem):
        vitem = models.VerificationItem()
        vitem.dias_status = 'Новая'
        vitem.author = request.user.extendeduser
        if item_type == 'person':
            vitem.person = item
        elif item_type == 'organization':
            vitem.organization = item
        elif item_type == 'short_item':
            vitem.short_item = item
            # vitem.dias_status = 'В работе'
            # vitem.case_officer = request.user.extendeduser
            vitem.author = request.user.extendeduser
        
        vitem.is_shadow = is_shadow
        new_vitem = vitem.save()
        if not related_vitem is None and len(related_vitem):
            vitem.related_vitem = related_vitem[0]
            related_vitem[0].related_vitem = vitem
            related_vitem[0].save()
            vitem.is_filled = related_vitem[0].is_filled
            new_vitem = vitem.save()
        return new_vitem

# Проверка сканов объекта, смена статус Заявки
def required_scan_checking(model_id, model_name, model_role=None):
    scan_list = models.DocStorage.objects.filter(model_name = model_name.title(), model_id = model_id).exclude(to_del = True)
    if model_name == 'person':
        if model_role in ['Ген. директор', 'Бенефициар']:
            return True
        doc_types = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Видеоприветствие']
    elif model_name == 'organization':
        if model_role == 'Контрагент':
            return True
        doc_types = ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет']
    elif model_name == 'short_item':
        return True
    
    is_filled = True
    
    for doc_type in doc_types:
        if scan_list.filter(doc_type = doc_type).count() == 0:
            is_filled = False
    return is_filled

def is_vitem_ready(item_type, item=None):
    if item_type == 'person':
        if item.role in ['Ген. директор', 'Бенифициар']:
            return False
    if item:
        if item_type == 'short_item':
            is_ready = True
        else:
            is_ready = required_scan_checking(getattr(item, item_type).id, item_type, item.role)
        if is_ready:
            if item_type == 'organization':
                ceo = models.PersonWithRole.objects.filter(related_organization = item, role = 'Ген. директор')
                if len(ceo) == 0:
                    is_ready = False

        vitem = models.VerificationItem.objects.filter(**{item_type: item})
        if len(vitem):
            if vitem[0].is_filled != is_ready:
                vitem[0].is_filled = is_ready
                vitem[0].save()

    return is_ready

def newChatMessage(vitem, message, author):
    new_msg = models.VitemChat()
    new_msg.vitem = vitem
    new_msg.msg = message
    new_msg.author = author
    new_msg.save()
    update_logger('VitemChat', new_msg.id, '', author)

def accessing(item_id, model_name, user):
    if item_id:
        item = getattr(models, model_name).objects.filter(id = item_id)
        if model_name == 'PersonWithRole':
            if not len(item):
                return False
            if item[0].role in ['Ген. директор', 'Бенефициар']:
                vitem = models.VerificationItem.objects.filter(organization__id = item[0].related_organization.id)
            else:
                vitem = models.VerificationItem.objects.filter(person__id = item_id)
        elif model_name == 'VerificationItem':
            vitem = item
        else:
            vitem = models.VerificationItem.objects.filter(organization__id = item_id)
        if len(item):
            if user.extendeduser.user_role.role_lvl <= 2:
                return True
            elif item[0].author.user_role == user.extendeduser.user_role:
                return True
            if len(vitem):
                if vitem[0].author.user_role == user.extendeduser.user_role:
                    return True
                elif vitem[0].case_officer:
                    if vitem[0].case_officer.user_role == user.extendeduser.user_role:
                        return True
                elif vitem[0].organization and user.extendeduser.user_role.role_lvl == 3:
                    return True
    else:
        return True
    return False

def send_mail(target_user, subject, body):
    new_msg = models.UserNotification(user = target_user, email_to = target_user.user.email, email_from = 'dias@finfort.ru', msg_theme = subject, msg = body)
    new_msg.save()
    msg = EmailMessage(
        subject=new_msg.msg_theme,
        body=new_msg.msg,
        from_email='sim@finfort.ru',
        to=(new_msg.email_to,),
        headers={'From': new_msg.email_from}
    )
    msg.content_subtype = 'html'
    msg.send()


def twin_detecter(model_name, param, item_role_name, author=None):
    filter = ['person', 'sneals'] if model_name == 'Person' else ['organization', 'inn']
    item_qs = getattr(models, f'{model_name}WithRole').objects.filter(**{f'{filter[0]}__{filter[1]}': param})
    if not len(item_qs):
        return []
    for item in item_qs:
        if item.role.role == item_role_name:
            return ['old', item]
    return ['new', getattr(item, filter[0])]
    
def object_wr_creater(request, model_name, obj, role):
    new_obj = getattr(models, f'{model_name}WithRole')()
    setattr(new_obj, model_name.lower(), obj)
    new_obj.author = request.user.extendeduser
    new_obj.role = role
    new_obj.save()
    return new_obj