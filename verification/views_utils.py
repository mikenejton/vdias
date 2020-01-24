from . import models
from django.db.models import Q
from django.core.mail import EmailMessage
from djqscsv import render_to_csv_response
class UserStats:
    def __init__(self):
        pass

# Базовый контекст для меню
def get_base_context(user):
    context = {}
    stats = UserStats()
    stats.q_all = models.VerificationItem.objects.all().order_by('-created')
    stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True)
    stats.q_mine = stats.q_all.filter(case_officer__user = user)
    stats.q_at_work = stats.q_all.filter(dias_status = 'В работе')
    stats.q_to_fix = stats.q_all.filter(to_fix = True)
    stats.q_fixed = stats.q_all.filter(fixed = True)
    stats.q_finished = stats.q_all.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
    stats.q_not_filled = stats.q_all.filter(is_filled = False, dias_status = 'Новая')
    if user.extendeduser.user_role.role_lvl == 2:
        stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True).filter(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент')) #????????? штатник и контрагент?
    if user.extendeduser.user_role.role_lvl == 3:
        stats.q_all = stats.q_all.exclude(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент')).exclude(Q(is_filled = False) and Q(dias_status = 'Новая'))
        stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True)
        stats.q_at_work = stats.q_mine.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_mine.filter(to_fix = True)
        stats.q_fixed = stats.q_mine.filter(fixed = True)
        stats.q_finished = stats.q_mine.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
        stats.q_not_filled = stats.q_mine.filter(is_filled = False, dias_status = 'Новая')
    elif user.extendeduser.user_role.role_lvl >= 4:
        stats.q_all = stats.q_all.filter(author__user_role = user.extendeduser.user_role)
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
            if getattr(old_set, i.name) != getattr(new_set, i.name):
                changes.append([i.name, getattr(new_set, i.name), getattr(old_set, i.name)])
        if len(changes) > 0:
            for i in changes:
                new_dl = models.DataLogger(model_name=model_name, model_id=pk, action='Обновление записи', field_name=i[0], new_value=i[1], old_value=i[2], author=username)
                new_dl.save()

def vitem_creater(request, item, item_type):
    print(f'{request} \n {item_type}:{item}')
    vitem = models.VerificationItem.objects.filter(**{item_type: item})
    if not len(vitem):
        vitem = models.VerificationItem()
        print(vitem)
        if item_type == 'person':
            vitem.person = item
        elif item_type == 'organization':
            vitem.organization = item
        vitem.dias_status = 'Новая'
        print(vitem)
        vitem.author = request.user.extendeduser
        vitem.save()
    
        


# Проверка сканов объекта, смена статус Заявки
def required_scan_checking(model_id, model_name):
    scan_list = models.DocStorage.objects.filter(model_name = model_name.title(), model_id = model_id).exclude(to_del = True)
    if model_name == 'person':
        doc_types = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета']
    elif model_name == 'organization':
        doc_types = ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет']
    
    is_filled = True
    
    for doc_type in doc_types:
        if scan_list.filter(doc_type = doc_type).count() == 0:
            is_filled = False
    return is_filled

def is_vitem_ready(item_type, item=None):
    if item_type == 'person':
        if item.person_role in ['Ген. директор', 'Бенифициар']:
            return False
    if item:
        is_ready = required_scan_checking(getattr(item, item_type).id, item_type)
        if is_ready:
            if item_type == 'organization':
                sub_items = models.PersonWithRole.objects.filter(related_organization = item)
                if len(sub_items):
                    for sub_item in sub_items:
                        sub_item_rsc = required_scan_checking(item.person.id, 'person')
                        if not sub_item_rsc:
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
                elif vitem[0].case_officer.user_role == user.extendeduser.user_role:
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

def export_csv(qs):
    return render_to_csv_response(qs)
