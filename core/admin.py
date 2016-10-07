from django.contrib import admin
from core.models import Contact, Organisation, Currency, Sector, Spreadsheet, Entry
# Register your models here.

class ContactInline(admin.TabularInline):
    model = Contact

class OrganisationAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ['name','grant_making','loan_making','government']
    inlines = [ContactInline,]
    prepopulated_fields = {'slug': ('name',), }
    #enable the save buttons on top of change form
    save_on_top = True
    
class CurrencyAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ['iso','description','symbol']
    #enable the save buttons on top of change form
    save_on_top = True
    
class ContactAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ['name','organisation']
    def name(self,obj):
        return obj.user.get_full_name()
    #enable the save buttons on top of change form
    save_on_top = True
    
class SectorAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ['name','loan_or_grant']
    #enable the save buttons on top of change form
    save_on_top = True
    
class SpreadsheetAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ["year","organisation","currency"]
    list_filter = ["year","organisation","currency"]
    #enable the save buttons on top of change form
    save_on_top = True
    
class EntryAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ["number"
                    ,"organisation"
                    ,"year"
                    ,"loan_or_grant"
                    ,"concessional"
                    ,"pledge_or_disbursement"
                    ,"recipient"
                    ,"sector"
                    ,"channel_of_delivery"
                    ,"refugee_facility_for_turkey"
                    ,"amount"
                    ]
    list_filter = ["spreadsheet__organisation"
                   ,"spreadsheet__year"
                    ,"loan_or_grant"
                    ,"concessional"
                    ,"pledge_or_disbursement"
                    ,"recipient"
                    ,"sector"
                    ,"channel_of_delivery"
                    ,"refugee_facility_for_turkey"
                    ]
    def number(self,obj):
        return obj.pk
    def organisation(self,obj):
        return obj.spreadsheet.organisation
    def year(self,obj):
        return obj.spreadsheet.year
    #enable the save buttons on top of change form
    save_on_top = True
    
admin.site.register(Organisation,OrganisationAdmin)
admin.site.register(Currency,CurrencyAdmin)
admin.site.register(Contact,ContactAdmin)
admin.site.register(Sector,SectorAdmin)
admin.site.register(Spreadsheet,SpreadsheetAdmin)
admin.site.register(Entry,EntryAdmin)