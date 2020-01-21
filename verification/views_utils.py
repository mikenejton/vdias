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
    stats.q_all = models.VerificationItem.objects.all()
    stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True)
    stats.q_mine = stats.q_all.filter(case_officer__user = user)
    stats.q_at_work = stats.q_all.filter(dias_status = 'В работе')
    stats.q_to_fix = stats.q_all.filter(to_fix = True)
    stats.q_fixed = stats.q_all.filter(fixed = True)
    stats.q_finished = stats.q_all.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
    stats.q_not_filled = stats.q_all.filter(is_filled = False)
    if user.extendeduser.user_role.role_lvl == 2:
        stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True).filter(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент')) #????????? штатник и контрагент?
    if user.extendeduser.user_role.role_lvl == 3:
        stats.q_all = stats.q_all.exclude(Q(person__person_role = 'Штатный сотрудник') | Q(organization__organization_role = 'Контрагент'))
        stats.q_new = stats.q_all.filter(dias_status = 'Новая', is_filled = True)
        stats.q_at_work = stats.q_mine.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_mine.filter(to_fix = True)
        stats.q_fixed = stats.q_mine.filter(fixed = True)
        stats.q_finished = stats.q_mine.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
        stats.q_not_filled = stats.q_mine.filter(is_filled = False)
    elif user.extendeduser.user_role.role_lvl >= 4:
        stats.q_all = stats.q_all.filter(author__user_role = user.extendeduser.user_role)
        stats.q_mine = stats.q_all.filter(author__user = user)
        stats.q_at_work = stats.q_mine.filter(dias_status = 'В работе')
        stats.q_to_fix = stats.q_mine.filter(to_fix = True)
        stats.q_fixed = stats.q_mine.filter(fixed = True)
        stats.q_finished = stats.q_mine.filter(dias_status__in=['Отказ', 'Одобрено', 'Одобрено, особый контроль'])
        stats.q_not_filled = stats.q_mine.filter(is_filled = False)
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

def required_scan_checking(scan):
        scan_list = models.DocStorage.objects.filter(model_name = scan.model_name, model_id = scan.model_id).exclude(to_del = True)
        if scan.model_name == 'Person':
            vitem = models.VerificationItem.objects.filter(person__person__id = scan.model_id)
            doc_types = ['Паспорт 1 страница', 'Паспорт 2 страница', 'Анкета']
        elif scan.model_name == 'Organization':
            vitem = models.VerificationItem.objects.filter(organization__organization__id = scan.model_id)
            doc_types = ['Скан анкеты', 'Скан устава', 'Скан свидетельства о гос.рег.', 'Скан свидетельства о постановке на налоговый учет']
        vitem_is_filled = True
        dias_status = 'Новая'
        if len(vitem):
            for doc_type in doc_types:
                if scan_list.filter(doc_type = doc_type).count() == 0:
                    vitem_is_filled = False
                    dias_status = ''
            vitem[0].is_filled = vitem_is_filled
            if vitem[0].dias_status == 'Новая' or vitem[0].dias_status == '':
                vitem[0].dias_status = dias_status
            vitem[0].save()

def newChatMessage(vitem, message, author):
    new_msg = models.VitemChat()
    new_msg.vitem = vitem
    new_msg.msg = message
    new_msg.author = author
    new_msg.save()
    utils.update_logger('VitemChat', new_msg.id, '', author)

def accessing(item_id, model_name, user):
    item = getattr(models, model_name).objects.filter(id = item_id)
    print(item)
    print(model_name)
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
    return False

def send_mail(email_to, subject, body):
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email='sim@finfort.ru',
        to=(email_to,),
        headers={'From': 'pj@finfort.ru'}
    )
    msg.content_subtype = 'html'
    msg.send()
    print(msg)