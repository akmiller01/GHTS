from django.forms import ModelForm
from core.models import Spreadsheet
        
class SpreadsheetForm(ModelForm):
    class Meta:
        model = Spreadsheet
        fields = ('currency','comment','multiyear_comment')