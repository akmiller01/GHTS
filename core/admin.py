from django.contrib import admin
from core.models import Contact, Organisation, Currency, Sector, Spreadsheet, Entry
# Register your models here.

def refresh_coordinates(modeladmin,request,queryset):
    for e in queryset:
        e.save()

class ContactInline(admin.TabularInline):
    model = Contact

class OrganisationAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ['name','grant_making','loan_making','government']
    inlines = [ContactInline,]
    prepopulated_fields = {'slug': ('name',), }
    filter_horizontal = ('sectors',)
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
    list_display = ['name','loan_or_grant','default']
    #enable the save buttons on top of change form
    save_on_top = True
    # normaluser_fields = ('name','loan_or_grant',)
    # superuser_fields = ('default',)
    # def get_form(self, request, obj=None, **kwargs):                             
    #     if request.user.is_superuser:                                            
    #         self.fields = self.normaluser_fields + self.superuser_fields         
    #     else:                                                                    
    #         self.fields = self.normaluser_fields
    #     return super(SectorAdmin, self).get_form(request, obj, **kwargs)
    
class SpreadsheetAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ["year","organisation","currency"]
    list_filter = ["year","organisation","currency"]
    #enable the save buttons on top of change form
    save_on_top = True
    
class EntryAdmin(admin.ModelAdmin):
    #fields display on change list
    list_display = ["number"
                    ,"prevfac"
                    ,"organisation"
                    ,"year"
                    ,"loan_or_grant"
                    ,"concessional"
                    ,"appeal"
                    ,"appeal_status"
                    ,"pledge_or_disbursement"
                    ,"recipient"
                    ,"sector"
                    ,"channel_of_delivery"
                    ,"facility"
                    ,"amount"
                    ]
    list_filter = ["prevfac","spreadsheet__organisation"
                   ,"spreadsheet__year"
                    ,"loan_or_grant"
                    ,"concessional"
                    ,"appeal"
                    ,"appeal_status"
                    ,"pledge_or_disbursement"
                    ,"recipient"
                    ,"sector"
                    ,"channel_of_delivery"
                    ,"facility"
                    ]
    actions = [refresh_coordinates]
    def prevfac(self,obj):
        return obj.facility_lookup()
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