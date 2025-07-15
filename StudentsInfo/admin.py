from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from . import models as StudentsModels
# Register your models here.

class StudentsInline(admin.StackedInline):
    model = StudentsModels.StudentUser
    can_delete = False
    verbose_name_plural = 'Students'
    extra=1

class UserAdmin(BaseUserAdmin):
    inlines = (StudentsInline,)
##############

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


    
@admin.register(StudentsModels.SignedCheck)
class SignedCheckAdmin(admin.ModelAdmin):
    list_display = ('student', 'amout', 'check_date', 'check_number', 'bank')
    list_filter = ('student', 'check_date', 'bank')
    fieldsets = (
        ("مشخصات چک", {
            'fields': (('student',), ('amout',), ('check_date',), ('check_number',), ('bank',), ('description',))
        }),
    )

@admin.register(StudentsModels.DirectMoney)
class DirectMoneyAdmin(admin.ModelAdmin):
    list_display = ('student', 'amout', 'payment_date', 'refrence_number', 'following_number', 'card_number', 'payment_method', 'bank')
    list_filter = ('student', 'payment_date', 'payment_method', 'bank')
    fieldsets = (
        ("مشخصات پرداخت نقدی", {
            'fields': (('student',), ('amout',), ('payment_date',), ('refrence_number',), ('following_number',), ('card_number',), ('payment_method',), ('bank',), ('description',))
        }),
    )    


    
@admin.register(StudentsModels.Books)
class BooksAdmin(admin.ModelAdmin):
    list_display = ('booksname',)
    list_filter = ('student', 'booksname')
    fieldsets = (
        ("مشخصات ", {
            'fields': (('student',), ('booksname',),)
        }),
    )