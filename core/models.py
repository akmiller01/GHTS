from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

class Currency(models.Model):
    symbol = models.CharField(max_length=10)
    iso = models.CharField(max_length=3)
    description = models.CharField(max_length=255)
    
    class Meta:
        ordering = ['iso']
        verbose_name_plural = "currencies"
    
    def __str__(self):
        return self.iso
    
class Sector(models.Model):
    name = models.CharField(max_length=255)
    LOAN_OR_GRANT_CHOICES = (
        ('L','Loan'),
        ('G','Grant'),
    )
    loan_or_grant = models.CharField(max_length=1,choices=LOAN_OR_GRANT_CHOICES,default='G')
    default = models.BooleanField(default=False)
    def loan_verbose(self):
        return dict(Transaction.LOAN_OR_GRANT_CHOICES)[self.loan_or_grant]
    
    def __unicode__(self):
        return u'%s' % self.name
    
    def save(self, *args, **kwargs):
        super(Sector, self).save(*args, **kwargs)
        if self.name:
            self.name = self.name.replace('"',"'")
        super(Sector, self).save(*args, **kwargs)

class Organisation(models.Model):
    name = models.CharField(max_length=255,unique=True)
    slug = models.SlugField(max_length=255,unique=True)
    grant_making = models.BooleanField(default=True)
    loan_making = models.BooleanField(default=True)
    government = models.BooleanField(default=True)
    bank = models.BooleanField(default=False)
    sectors = models.ManyToManyField(Sector,related_name="sectors",related_query_name="sector",blank=True)
    disable_default_loan_sectors = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
    
    def __unicode__(self):
        return u'%s' % self.name
    
    def get_absolute_url(self):
        return reverse("core.views.adminEdit",args=[self.slug,2016])
    
    def get_export_url(self):
        return reverse("core.views.csv",args=[self.slug])

class Contact(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True)
    organisation = models.ForeignKey(Organisation)
    
    def __str__(self):
        return self.user.get_full_name()
    
    def __unicode__(self):
        return u'%s' % self.user.get_full_name()
    
class Spreadsheet(models.Model):
    YEAR_CHOICES = (
        (2016,2016),
        (2017,"2017-2020"),
        (2,"2018-2020"),
        (1,2017),
        (3,2018),
        (4,"2019-2020")
    )
    year = models.IntegerField(choices=YEAR_CHOICES)
    currency = models.ForeignKey(Currency)
    organisation = models.ForeignKey(Organisation)
    comment = models.TextField(null=True,blank=True)
    multiyear_comment = models.TextField(null=True,blank=True)
    
    def get_absolute_url(self):
        return reverse("core.views.edit",args=[self.year])
    
    def year_translate(self):
        val = self.year
        if val is None or val=="":
            return ""
        else:
            return dict(Spreadsheet.YEAR_CHOICES)[val]
    
class Entry(models.Model):
    coordinates = models.CharField(max_length=300,editable=False)
    amount = models.DecimalField(max_digits=99, decimal_places=2,blank=True,null=True)
    spreadsheet = models.ForeignKey(Spreadsheet,editable=False)
    LOAN_OR_GRANT_CHOICES = (
        ('L','Loan'),
        ('G','Grant'),
    )
    PLEDGE_OR_DISB_CHOICES = (
        ('P','Pledged'),
        ('M','Committed'),
        ('C','Contracted'),
        ('D','Disbursed'),
    )
    RECIPIENT_CHOICES = (
        ('S','Syria'),
        ('J','Jordan'),
        ('L','Lebanon'),
        ('T','Turkey'),
        ('I','Iraq'),
        ('E','Egypt'),
        ('M','Multi-country'),
        ('R','Region'),
        ('N','Not defined'),
    )
    DELIVERY_CHOICES = (
        ('U','UN agencies'),
        ('N','NGOs'),
        ('R','RCRC'),
        ('G','Partner country government'),
        ('P','Private sector'),
        ('O','Other channel of delivery (please detail in the comments box)'),
    )
    FACILITY_CHOICES = (
        ('L','Facility for Refugees in Turkey'),
        ('E','EU Regional Trust Fund in response to the Syrian crisis'),
        ('G','Global Concessional Financing Facility')
    )
    APPEAL_STATUS_CHOICES = (
        ('P','Amount pledged for appeal'),
        ('V','How much of the appeal pledge via conference pledge'),
        ('C','Contributions for UN-coordinated appeals so far'),
        ('H','Contributions via appeal part of conference pledge'),
    )
    loan_or_grant = models.CharField(max_length=1,choices=LOAN_OR_GRANT_CHOICES,blank=True,null=True)
    concessional = models.BooleanField(default=True)
    appeal = models.BooleanField(default=False)
    appeal_status = models.CharField(max_length=1,choices=APPEAL_STATUS_CHOICES,blank=True,null=True)
    pledge_or_disbursement = models.CharField(max_length=1,choices=PLEDGE_OR_DISB_CHOICES,blank=True,null=True)
    recipient = models.CharField(max_length=1,choices=RECIPIENT_CHOICES,default="N")
    channel_of_delivery = models.CharField(max_length=1,choices=DELIVERY_CHOICES,blank=True,null=True)
    sector = models.ForeignKey(Sector,blank=True,null=True)
    facility = models.CharField(max_length=1,choices=FACILITY_CHOICES,blank=True,null=True)
    def loan_or_grant_lookup(self):
        val = self.coordinates.split("|")[0]
        return val
    def concessional_lookup(self):
        val = self.coordinates.split("|")[1]
        return val=="C"
    def pledge_or_disbursement_lookup(self):
        val = self.coordinates.split("|")[2]
        return val
    def recipient_lookup(self):
        val = self.coordinates.split("|")[3]
        return val
    def sector_lookup(self):
        val = self.coordinates.split("|")[4]
        return val
    def channel_of_delivery_lookup(self):
        val = self.coordinates.split("|")[5]
        return val
    def facility_lookup(self):
        val = self.coordinates.split("|")[6]
        return val
    def appeal_lookup(self):
        val = self.coordinates.split("|")[7]
        return val=="A"
    def appeal_status_lookup(self):
        val = self.coordinates.split("|")[8]
        return val
    def loan_or_grant_translate(self):
        val = self.coordinates.split("|")[0]
        if val is None or val=="":
            return ""
        else:
            return dict(Entry.LOAN_OR_GRANT_CHOICES)[val]
    def concessional_translate(self):
        val = self.coordinates.split("|")[1]
        return val=="C"
    def pledge_or_disbursement_translate(self):
        val = self.coordinates.split("|")[2]
        if val is None or val=="":
            return ""
        else:
            return dict(Entry.PLEDGE_OR_DISB_CHOICES)[val]
    def recipient_translate(self):
        val = self.coordinates.split("|")[3]
        if val is None or val=="":
            return ""
        else:
            return dict(Entry.RECIPIENT_CHOICES)[val]
    def sector_translate(self):
        val = self.coordinates.split("|")[4]
        return val
    def channel_of_delivery_translate(self):
        val = self.coordinates.split("|")[5]
        if val is None or val=="":
            return ""
        else:
            return dict(Entry.DELIVERY_CHOICES)[val]
    def facility_translate(self):
        val = self.coordinates.split("|")[6]
        if val is None or val=="":
            return ""
        else:
            return dict(Entry.FACILITY_CHOICES)[val]
    def appeal_translate(self):
        val = self.coordinates.split("|")[7]
        return val=="A"
    def appeal_status_translate(self):
        val = self.coordinates.split("|")[8]
        if val is None or val=="":
            return ""
        else:
            return dict(Entry.APPEAL_STATUS_CHOICES)[val]
    class Meta:
        verbose_name_plural = "entries"
        
    def save(self, *args, **kwargs):
        #Coordinates are grant|concess|pledge|recip|sector|channel|facility
        coord_list = [
            self.loan_or_grant if self.loan_or_grant else ""
            ,"C" if self.concessional else "N"
            ,self.pledge_or_disbursement if self.pledge_or_disbursement else ""
            ,self.recipient if self.recipient else ""
            ,self.sector.__unicode__() if self.sector else ""
            ,self.channel_of_delivery if self.channel_of_delivery else ""
            ,self.facility if self.facility else ""
            ,"A" if self.appeal else "N"
            ,self.appeal_status if self.appeal_status else ""
        ]
        self.coordinates = "|".join(coord_list)
        super(Entry, self).save(*args, **kwargs)
        
    def save_reverse(self, *args, **kwargs):
        self.loan_or_grant = self.loan_or_grant_lookup()
        self.concessional = self.concessional_lookup()
        self.pledge_or_disbursement =  self.pledge_or_disbursement_lookup()
        self.recipient = self.recipient_lookup()
        self.channel_of_delivery = self.channel_of_delivery_lookup()
        if Sector.objects.filter(name=self.sector_lookup(),loan_or_grant=self.loan_or_grant_lookup()).exists():
            self.sector = Sector.objects.filter(name=self.sector_lookup(),loan_or_grant=self.loan_or_grant_lookup()).first()
        self.refugee_facility_for_turkey = self.facility_lookup()
        self.appeal = self.appeal_lookup()
        self.appeal_status = self.appeal_status_lookup()
        super(Entry, self).save(*args, **kwargs)


