from datetime import datetime
from django.utils.timezone import get_current_timezone
from django.db import models
from django.contrib.auth.models import User

# Directories
class Division(models.Model):
    division = models.CharField('Подразделение', max_length = 200)
    division_name = models.CharField('Имя подразделения', max_length = 200)
    
    def __str__(self):
        return self.division_name

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'

class StaffDepartment(models.Model):
    dep_name = models.CharField('Отдел', max_length = 400)
    dep_leader = models.CharField('Руководитель', max_length = 400)
    
    def __str__(self):
        return f'{self.dep_name} ({self.dep_leader})'

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

class Manager(models.Model):
    fio = models.CharField('ФИО', max_length = 200)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, verbose_name = 'Подразделение', blank=True, null=True)
    is_active = models.BooleanField('Активен', default=True)

    def __str__(self):
        return f'{self.fio} ({self.division})'

    class Meta:
        verbose_name = 'Менеджер'
        verbose_name_plural = 'Менеджеры'

class ObjectRole(models.Model):
    role = models.CharField('Роль', max_length = 200)
    role_name = models.CharField('Имя роли', max_length = 200)
    
    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name = 'Роль объекта'
        verbose_name_plural = 'Роли объектов'

class ObjectFormField(models.Model):
    role = models.ForeignKey(ObjectRole, on_delete=models.CASCADE, verbose_name = 'Роль')
    field_name = models.CharField('Поле', max_length = 200)
    is_required = models.BooleanField('Обязательность', default=False)
    field_translate = models.CharField('Перевод', max_length = 200, null=True, blank=True)
    def __str__(self):
        return self.field_name
    class Meta:
        verbose_name = 'Поле формы'
        verbose_name_plural = 'Поля формы'

class DiasStatus(models.Model):
    status = models.CharField('Статус', max_length = 200)
    is_hidden = models.BooleanField('Скрытый', default=False)
    check_required = models.BooleanField('Требует проверки полей', default=False)
    def __str__(self):
        return self.status
    class Meta:
        verbose_name = 'Статус ДИАС'
        verbose_name_plural = 'Статусы ДИАС'

class PartnerShipStatus(models.Model):
    status = models.CharField('Статус', max_length = 200)
    def __str__(self):
        return self.status
    class Meta:
        verbose_name = 'Статус сотрудничества'
        verbose_name_plural = 'Статусы сотрудничества'


class ProductType(models.Model):
    product_type = models.CharField('Тип продуктов', max_length = 200)
    def __str__(self):
        return self.product_type
    class Meta:
        verbose_name = 'Тип продуктов'
        verbose_name_plural = 'Типы продуктов'


# -----------------------------------------------------------

# User's extends
class UserRole(models.Model):
    role_lvl = models.IntegerField('Уровень роли ')
    role_name = models.CharField('Роль', max_length = 200)
    role_description = models.CharField('Описание', max_length = 1000)
    def __str__(self):
        return self.role_name
    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'

class ExtendedUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_role = models.ForeignKey(UserRole, on_delete=models.PROTECT)
    access_lvl = models.IntegerField('Уровень доступа')
    def __str__(self):
        return ' '.join(filter(None, [self.user.last_name, self.user.first_name]))

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
# -----------------------------------------------------------


# Базовые модели
class Organization(models.Model):
    org_form = models.CharField('Орг форма', max_length = 100)
    org_name = models.CharField('Название', max_length = 500)
    full_name = models.CharField('Полное название', max_length = 500, blank=True, null=True)
    adr_reg = models.CharField('Юридический адрес', max_length=500, blank=True, null=True)
    adr_fact = models.CharField('Фактический адрес', max_length=500, blank=True, null=True)
    inn = models.CharField('ИНН', max_length = 12, blank=True, null=True, unique=True)
    ogrn = models.CharField('ОГРН', max_length = 15, blank=True, null=True, unique=True)
    phone_number = models.CharField('Телефон', max_length = 200, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    media_folder = models.CharField('Папка организации', max_length = 1000, blank=True, null=True)
    comment = models.TextField('Примечание', default='', blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        self.full_name = ' '.join(filter(None, [self.org_form, self.org_name])).upper()
        super().save(*args, **kwargs)
        return self.id
    
    def __str__(self):
        return f'{self.full_name}, ИНН {self.inn}'
    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

class OrganizationWithRole(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.ForeignKey(ObjectRole, on_delete=models.PROTECT, verbose_name = 'Роль')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, verbose_name = 'Подразделение', blank=True, null=True)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT, verbose_name = 'Тип продуктов', blank=True, null=True)
    partnership_status = models.ForeignKey(PartnerShipStatus, on_delete=models.PROTECT, verbose_name = 'Статус сотрудничества', blank=True, null=True)
    verificated = models.BooleanField('Верифицировано', default=False)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return self.id

    def __str__(self):
        return f'{self.organization.full_name}, {self.role}'

    class Meta:
        verbose_name = 'Роль организации'
        verbose_name_plural = 'Роли организаций'

class Person(models.Model):
    fio = models.CharField('ФИО', max_length=500, blank=True)
    last_name = models.CharField('Фамилия', max_length=300)
    first_name = models.CharField('Имя', max_length=300)
    patronymic = models.CharField('Отчетство', max_length=300, blank=True, null=True)
    prev_fio = models.CharField('Предыдущее ФИО', max_length=500, blank=True, null=True)
    dob = models.DateField('Дата рождения', blank=True, null=True)
    pob = models.CharField('Место рождения', max_length=300, blank=True, null=True)
    adr_reg = models.CharField('Адрес регистрации', max_length=500, blank=True, null=True)
    adr_fact = models.CharField('Адрес проживания', max_length=500, blank=True, null=True)
    city = models.CharField('Город', max_length=500, blank=True, null=True)
    pass_sn = models.CharField('Серия-номер паспорта', max_length=11, blank=True, null=True, unique=True)
    pass_date = models.DateField('Дата выдачи', blank=True, null=True)
    pass_org = models.CharField('Кем выдан', max_length=500, blank=True, null=True)
    pass_code = models.CharField('Код подразделения', max_length=7, blank=True, null=True)
    sneals = models.CharField('СНИЛС', max_length = 14, blank=True, null=True, unique=True)
    phone_number = models.CharField('Телефон', max_length = 200, blank=True, null=True, unique=True)
    email = models.EmailField('Email', blank=True, null=True)
    staff_dep = models.ForeignKey(StaffDepartment, on_delete=models.SET_NULL, verbose_name='Отдел', blank=True, null=True)
    staff_position = models.CharField('Должность', max_length = 300, blank=True, null=True)
    comment = models.TextField('Примечание', default='', blank=True, null=True)
    media_folder = models.CharField('Папка физ.лица', max_length = 1000, blank=True, null=True)
    video_upload_date = models.DateField('Дата загрузки видео', blank=True, null=True)
    video_check_date = models.DateField('Дата проверки видео', blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        self.fio = ' '.join(filter(None, [self.last_name, self.first_name, self.patronymic])).upper()
        super().save(*args, **kwargs)
        return self.id
    
    def __str__(self):
        return self.fio
    
    class Meta:
        unique_together = [['last_name', 'first_name', 'patronymic', 'dob']]
        verbose_name = 'Физ.лицо'
        verbose_name_plural = 'Физ.лица'

class PersonWithRole(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.ForeignKey(ObjectRole, on_delete=models.PROTECT, verbose_name = 'Роль')
    verificated = models.BooleanField('Верифицирован', default=False)
    related_manager = models.ForeignKey(Manager, on_delete=models.PROTECT, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, verbose_name = 'Подразделение', blank=True, null=True)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT, verbose_name = 'Тип продуктов', blank=True, null=True)
    partnership_status = models.ForeignKey(PartnerShipStatus, on_delete=models.PROTECT, verbose_name = 'Статус сотрудничества', blank=True, null=True)
    staff_status = models.CharField('Статус сотрудника', max_length=300, blank=True, null=True)
    related_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return self.id

    def __str__(self):
        return str(f'{self.person} ({self.role})')

    class Meta:
        verbose_name = 'Роль физ.лица'
        verbose_name_plural = 'Роли физ.лиц'

class ShortItem(models.Model):
    item_id = models.CharField('Системный ID', max_length=300, unique=True)
    item_ref = models.CharField('Ссылка', max_length=300, unique=True)
    role = models.CharField('Роль', max_length=300)
    verificated = models.BooleanField('Верифицирован', default=False)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return self.id

    def __str__(self):
        return str(f'{self.role} - {self.item_id}')

    class Meta:
        verbose_name = 'Короткая заявка'
        verbose_name_plural = 'Короткие заявки'

class VerificationItem(models.Model):
    person = models.ForeignKey(PersonWithRole, on_delete=models.CASCADE, blank = True, null = True)
    organization = models.ForeignKey(OrganizationWithRole, on_delete=models.CASCADE, blank = True, null = True)
    short_item = models.ForeignKey(ShortItem, on_delete=models.CASCADE, blank = True, null = True)
    is_filled = models.BooleanField('Заявка заполнена', default=False)
    
    status = models.ForeignKey(DiasStatus, on_delete=models.SET_NULL, blank = True, null = True)
    to_fix = models.BooleanField('На доработке', default=False)
    fixed = models.BooleanField('Доработано', default=False)
    dias_comment = models.TextField('Комментарий ДИАС', blank=True, null=True, default='')
    case_officer = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='CaseOfficer', blank=True, null=True, verbose_name='Исполнитель')
    related_vitem = models.ForeignKey('self', on_delete = models.SET_NULL, related_name = "ShadowVitem", blank=True, null=True, verbose_name='Связанная заявка')
    is_shadow = models.BooleanField('Ведомая заявка', default=False)
    fms_not_ok = models.CharField('ФМС', max_length = 300, blank=True, null=True, default='')
    rosfin = models.CharField('Росфинмониторинг', max_length = 300, blank=True, null=True, default='')
    docs_full = models.CharField('Полнота и качество документов', max_length = 300, blank=True, null=True, default='')
    reg_checked = models.CharField('Постоянная регистрация', max_length = 300, blank=True, null=True, default='')
    
    cronos_status = models.CharField('Кронос статус', max_length = 300, blank=True, null=True)
    cronos = models.TextField('Кронос комментарий', blank=True, null=True, default='')
    fssp_status = models.CharField('ФССП статус', max_length = 300, blank=True, null=True, default='')
    fssp = models.TextField('ФССП', blank=True, null=True, default='')
    bankruptcy_status = models.CharField('Сайт по банкротству статус', max_length = 300, blank=True, null=True, default='')
    bankruptcy = models.TextField('Сайт по банкротству', blank=True, null=True, default='')
    court_status = models.CharField('Суды статус', max_length = 300, blank=True, null=True, default='')
    court = models.TextField('Суды', blank=True, null=True, default='')
    contur_focus_status = models.CharField('Контур-Фокус статус', max_length = 300, blank=True, null=True, default='')
    contur_focus = models.TextField('Контур-Фокус', blank=True, null=True, default='')
    affiliation_status = models.CharField('Проверка на аффилированность статус', max_length = 300, blank=True, null=True, default='')
    affiliation = models.TextField('Проверка на аффилированность', blank=True, null=True, default='')
    soc_status = models.CharField('Соцсети', max_length = 300, blank=True, null=True, default='')
    soc = models.TextField('Соцсети', blank=True, null=True, default='')

    edited = models.DateTimeField('Дата изменения', null=True, blank=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, prev_vitem=None, *args, **kwargs):
        if self.fixed:
            self.to_fix = False
        if self.to_fix:
            self.fixed = False
        self.edited = datetime.now(tz=get_current_timezone())
        if self.related_vitem:
            if (prev_vitem is None or prev_vitem != self.related_vitem) and self.related_vitem.related_vitem == self:
                for i in ['status', 'dias_comment', 'case_officer', 'fms_not_ok', 'docs_full', 'reg_checked', 'rosfin', 'cronos', 'cronos_status', 'fssp', 'fssp_status', 'bankruptcy', 'bankruptcy_status', 'court', 'court_status', 'contur_focus', 'contur_focus_status', 'affiliation', 'affiliation_status']:
                    if getattr(self.related_vitem, i) != getattr(self, i):
                        setattr(self.related_vitem, i, getattr(self, i))
                self.related_vitem.save(prev_vitem=self)
        super().save(*args, **kwargs)
        return self.id
    
    def __str__(self):
        caption = ''
        if self.person:
            caption = str(self.person)
        elif self.organization:
            caption = str(self.organization)
        elif self.short_item:
            caption = str(self.short_item)
        else:
            caption = 'No verification item..'
        return caption
    class Meta:
        verbose_name = 'Заявка на верификацию'
        verbose_name_plural = 'Заявки на верификацию'

class VitemChat(models.Model):
    vitem = models.ForeignKey(VerificationItem, on_delete=models.CASCADE)
    msg = models.TextField('Сообщение')
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, related_name='MsgAuthor', verbose_name='Пользователь')
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return self.id
    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чат'

# -----------------------------------------------------------

# Хранилище документов
def doc_path_maker(instance, filename):
    timestamp = datetime.strftime(datetime.now(), '%d%m%Y_%H%M%S')
    if instance.model_name == 'Person':
        obj_name = Person.objects.get(id = instance.model_id).fio
    else:
        obj_name = Organization.objects.get(id = instance.model_id).full_name
    f_name = ''.join([instance.doc_type.replace(' ', '_'), '_', timestamp, '.', filename.split('.')[-1]])
    return f'{instance.model_name}/{obj_name}_{instance.model_id}/{f_name}'

class DocStorage(models.Model):
    model_id = models.CharField('ID модели', max_length = 50)
    model_name = models.CharField('Модель', max_length = 200)
    doc_type = models.CharField('Тип документа', max_length = 300)
    file_name = models.CharField('Имя файла', max_length = 300, blank=True)
    scan_file = models.FileField(upload_to=doc_path_maker, verbose_name='Путь к файлу')
    scan = models.BooleanField('Скан', default=False)
    original = models.BooleanField('Оригинал', default=False)
    accepted = models.BooleanField('Проверен', default=False)
    to_del = models.BooleanField('На удаление', default=False)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Автор')
    def save(self, *args, **kwargs):
        timestamp = datetime.strftime(datetime.now(), '%d%m%Y_%H%M%S')
        self.file_name = ''.join([self.doc_type.replace(' ', '_'), '_', timestamp, '.', self.scan_file.name.split('.')[-1]])
        super().save(*args, **kwargs)
        return self.id
    
    def __str__(self):
        return f'{self.model_id} {self.model_name} {self.doc_type}'
    class Meta:
        verbose_name = 'Скан'
        verbose_name_plural = 'Сканы'

# -----------------------------------------------------------

# Уведомления пользователя - непонятно, нужно ли
class UserNotification(models.Model):
    user = models.ForeignKey(ExtendedUser, on_delete=models.PROTECT, verbose_name='Пользователь')
    email_to = models.CharField('Адрес', max_length=300)
    email_from = models.CharField('Отправлено от', max_length=300)
    msg_theme = models.CharField('Тема уведомления', max_length=300)
    msg = models.TextField('Уведомление')
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
    
    def __str__(self):
        return '{}: {}'.format(self.email_to, self.msg_theme)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        return self.id
# -----------------------------------------------------------

# Логирование действий
class DataLogger(models.Model):
    model_name = models.CharField('Модель', max_length = 300, blank=True, null=True)
    model_id = models.BigIntegerField('ID записи', blank=True, null=True)
    action = models.CharField('Действие', max_length=500, null=True, blank=True)
    field_name = models.CharField('Название поля', max_length=300, null=True, blank=True)
    new_value = models.CharField('Новое значение', max_length=500, null=True, blank=True)
    old_value = models.CharField('Старое значение', max_length=500, null=True, blank=True)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    author = models.ForeignKey(ExtendedUser, on_delete=models.SET_NULL, null=True, verbose_name='Пользователь')
    def __str__(self):
        return f'{self.model_name} {self.created}'

# -----------------------------------------------------------