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

class Organisation(models.Model):
    name = models.CharField(max_length=255,unique=True)
    slug = models.SlugField(max_length=255,unique=True)
    grant_making = models.BooleanField(default=True)
    loan_making = models.BooleanField(default=True)
    government = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __unicode__(self):
        return u'%s' % self.name
    
    def get_absolute_url(self):
        return reverse("core.views.csv",args=[self.slug])

class Contact(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True)
    organisation = models.ForeignKey(Organisation)
    
    def __str__(self):
        return self.user.get_full_name()
    
    def __unicode__(self):
        return u'%s' % self.user.get_full_name()
    
class Sector(models.Model):
    name = models.CharField(max_length=255)
    LOAN_OR_GRANT_CHOICES = (
        ('L','Loan'),
        ('G','Grant'),
    )
    loan_or_grant = models.CharField(max_length=1,choices=LOAN_OR_GRANT_CHOICES,default='G')
    def loan_verbose(self):
        return dict(Transaction.LOAN_OR_GRANT_CHOICES)[self.loan_or_grant]
    
    def __unicode__(self):
        return u'%s' % self.name
    
    def save(self, *args, **kwargs):
        super(Sector, self).save(*args, **kwargs)
        if self.name:
            self.name = self.name.replace('"',"'")
        super(Sector, self).save(*args, **kwargs)
    
class Spreadsheet(models.Model):
    YEAR_CHOICES = (
        (2016,2016),
        (2017,2017),
        (2018,2018),
        (2019,2019),
        (2020,2020),
    )
    year = models.IntegerField(choices=YEAR_CHOICES)
    currency = models.ForeignKey(Currency)
    organisation = models.ForeignKey(Organisation)
    comment = models.TextField(null=True,blank=True)
    
    def get_absolute_url(self):
        return reverse("core.views.edit",args=[self.year])
    
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
        ('I','Iraq'),
        ('E','Egypt'),
        ('T','Turkey'),
        ('R','Region'),
        ('N','Not defined'),
    )
    DELIVERY_CHOICES = (
        ('U','UN agencies'),
        ('N','NGOs'),
        ('R','RCRC'),
        ('G','Government institutions'),
        ('P','Private sector'),
        ('O','Other channel of delivery'),
    )
    loan_or_grant = models.CharField(max_length=1,choices=LOAN_OR_GRANT_CHOICES,blank=True,null=True)
    concessional = models.BooleanField(default=True)
    pledge_or_disbursement = models.CharField(max_length=1,choices=PLEDGE_OR_DISB_CHOICES,blank=True,null=True)
    recipient = models.CharField(max_length=1,choices=RECIPIENT_CHOICES,default="N")
    channel_of_delivery = models.CharField(max_length=1,choices=DELIVERY_CHOICES,blank=True,null=True)
    sector = models.ForeignKey(Sector,blank=True,null=True)
    refugee_facility_for_turkey = models.BooleanField(default=False)
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
        return val=="F"
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
        return val=="F"

    class Meta:
        verbose_name_plural = "entries"
        
    def save(self, *args, **kwargs):
        #Coordinates are grant|concess|pledge|recip|sector|channel|facility
        coord_list = [
            self.loan_or_grant if self.loan_or_grant else ""
            ,"C" if self.concessional else "N"
            ,self.pledge_or_disbursement if self.pledge_or_disbursement else ""
            ,self.recipient if self.recipient else ""
            ,self.sector if self.sector else ""
            ,self.channel_of_delivery if self.channel_of_delivery else ""
            ,"F" if self.refugee_facility_for_turkey else ""
        ]
        self.coordinates = "|".join(coord_list)
        super(Entry, self).save(*args, **kwargs)
        
    def save_reverse(self, *args, **kwargs):
        self.loan_or_grant = self.loan_or_grant_lookup()
        self.concessional = self.concessional_lookup()
        self.pledge_or_disbursement =  self.pledge_or_disbursement_lookup()
        self.recipient = self.recipient_lookup()
        self.channel_of_delivery = self.channel_of_delivery_lookup()
        if Sector.objects.filter(name=self.sector_lookup()).exists():
            self.sector = Sector.objects.get(name=self.sector_lookup())
        self.refugee_facility_for_turkey = self.facility_lookup()
        super(Entry, self).save(*args, **kwargs)


