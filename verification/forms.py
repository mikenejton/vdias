from django.forms import ModelForm
from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime
from math import floor
from . import models, views_utils

class PersonForm(ModelForm):
    class Meta:
        model = models.Person
        fields = '__all__'
    def clean(self):
        cleaned_data=super(PersonForm, self).clean()
        if cleaned_data.get('dob'):
            date_diff = datetime.now().date() - cleaned_data.get('dob')
            if floor(date_diff.days/365.25)  < 16:
                raise ValidationError({'dob': 'Возраст менее 16-ти лет!'})
            elif floor(date_diff.days/365.25)  > 99:
                raise ValidationError({'dob': 'Возраст более 99-ти лет!'})
            if cleaned_data.get('pass_date'):
                date_diff = cleaned_data.get('pass_date') - cleaned_data.get('dob')
                if floor(date_diff.days/365.25)  < 14:
                    raise ValidationError({'pass_date': 'Ошибка в дате выдачи паспорта (разница с датой рождения менее 14 лет!'})
        if cleaned_data.get('sneals'):
            result = views_utils.sneals_checking(cleaned_data.get('sneals'))
            if not result:
                raise ValidationError({'sneals': 'СНИЛС не соответствует правилам ПФР'})
        
class SearchForm(forms.Form):
    sneals = forms.CharField(max_length=14, required=False)
    inn = forms.CharField(max_length=12, required=False)

    def clean(self):
        cleaned_data=super(SearchForm, self).clean()
        if cleaned_data.get('sneals'):
            result = views_utils.sneals_checking(cleaned_data.get('sneals'))
            if not result:
                raise ValidationError({'sneals': 'СНИЛС не соответствует правилам ПФР'})

class OrganizationForm(ModelForm):
    class Meta:
        model = models.Organization
        fields = '__all__'

class DocStorageForm(ModelForm):
    class Meta:
        model = models.DocStorage
        fields = ('model_id', 'model_name', 'doc_type', 'scan_file', 'author')

class VerificationItemForm(ModelForm):
    class Meta:
        model = models.VerificationItem
        fields = ('status', 'dias_comment', 'case_officer', 'original_post_date', 'is_original_posted', 'fms_not_ok', 'docs_full', 'reg_checked', 'rosfin', 'cronos', 'cronos_status', 'fssp', 'fssp_status', 'bankruptcy', 'bankruptcy_status', 'court', 'court_status', 'contur_focus', 'contur_focus_status', 'affiliation', 'affiliation_status', 'soc', 'soc_status')

class PersonWithRoleForm(ModelForm):
    class Meta:
        model = models.PersonWithRole
        fields = '__all__'

class OrganizationWithRoleForm(ModelForm):
    class Meta:
        model = models.OrganizationWithRole
        fields = '__all__'

class ShortItemForm(ModelForm):
    class Meta:
        model = models.ShortItem
        fields = '__all__'