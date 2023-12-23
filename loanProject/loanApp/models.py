from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import shortuuid


class CustomUser(AbstractUser):
    is_admin= models.BooleanField('Is admin', default=False)
    is_customer = models.BooleanField('Is customer', default=False)
    image = models.FileField(upload_to='', null=True, blank=True)


class SavedModel(models.Model):
    name = models.CharField(max_length=50)
    file_path = models.CharField(max_length=255)
    
    

class UserDetail(models.Model):
    userID = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=30)
    lastName = models.CharField(max_length=30)
    job = models.CharField(max_length=30, null=True)
    salary = models.FloatField(null=True)
    image = models.FileField(upload_to='profile', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True) 
    
    def __str__(self):
        return self.firstName + " " + self.lastName


class LoanApplicant(models.Model):
    LoanID = models.CharField(max_length=12, primary_key=True, default=shortuuid.uuid)
    Age = models.IntegerField() 
    Income = models.FloatField()
    LoanAmount = models.FloatField()
    CreditScore = models.IntegerField()
    MonthsEmployed = models.IntegerField()
    LoanTerm = models.IntegerField()
    DTIRatio = models.FloatField()
    Default = models.IntegerField(null=True, blank=True)
    
    
User = get_user_model()

class NewLoanApplicant(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
    ]

    LoanID = models.CharField(max_length=12, primary_key=True, default=shortuuid.uuid)
    Age = models.IntegerField()
    Income = models.FloatField()
    LoanAmount = models.FloatField()
    CreditScore = models.IntegerField()
    MonthsEmployed = models.IntegerField()
    LoanTerm = models.IntegerField()
    DTIRatio = models.FloatField()
    Default = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')

    def __str__(self):
        return f"Loan Application {self.LoanID} by {self.user.username} - Status: {self.status}"