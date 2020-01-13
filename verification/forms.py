from django.forms import ModelForm
from . import models

class PersonForm(ModelForm):
    class Meta:
        model = models.Person
        fields = '__all__'
        
class PersonWithRoleForm(ModelForm):
    class Meta:
        model = models.PersonWithRole
        fields = '__all__'

class DocStorageForm(ModelForm):
    class Meta:
        model = models.DocStorage
        fields = ('model_id', 'model_name', 'doc_type', 'scan_file', 'author')

class VerificationItemForm(ModelForm):
    class Meta:
        model = models.VerificationItem
        fields = ('dias_status', 'to_fix', 'fixed', 'dias_comment', 'case_officer', 'cronos', 'fms_not_ok', 'rosfin', 'fssp', 'docs_full', 'bankruptcy', 'сourt', 'contur_focus', 'affiliation')