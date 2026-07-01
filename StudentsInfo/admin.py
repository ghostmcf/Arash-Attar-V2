from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from . import models as StudentsModels
# Register your models here
from .models import Notification, UserNotification
from django.utils.html import format_html

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
    
    




class UserNotificationInline(admin.TabularInline):
    model = UserNotification
    extra = 0
    readonly_fields = ('user', 'notification')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_persistent', 'is_finished', 'created_at')
    list_filter = ('is_persistent', 'is_finished')
    search_fields = ('title', 'message')
    filter_horizontal = ('groups',)  # برای انتخاب چند گروه راحت

    inlines = [UserNotificationInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and not obj.is_persistent:
            users = set(User.objects.filter(groups__in=obj.groups.all()).distinct())
            UserNotification.objects.bulk_create([UserNotification(user=u, notification=obj) for u in users])

    def status_action(self, obj):
        if not obj.is_finished:
            return format_html('<a class="button" href="{}">Mark Finished</a>', f'finish/{obj.id}/')
        return "Finished"
    status_action.short_description = "Action"


@admin.register(StudentsModels.TokenSession)
class TokenSessionAdmin(admin.ModelAdmin):
    """نمایش/لغوِ نشست‌های فعال برای superuser (حذفِ ردیف = خروجِ آن دستگاه)."""
    list_display = ('user', 'device', 'ip_address', 'country', 'created', 'last_used')
    list_filter = ('device', 'country')
    search_fields = ('user__username', 'ip_address', 'user_agent')
    readonly_fields = ('user', 'token_key', 'token_digest', 'ip_address', 'user_agent',
                       'device', 'country', 'created', 'last_used')

    def has_add_permission(self, request):
        return False

    # حذف از ادمین = لغوِ واقعیِ توکن (وگرنه فقط متادیتا پاک می‌شد و دستگاه لاگین می‌ماند)
    def delete_model(self, request, obj):
        from knox.models import AuthToken
        AuthToken.objects.filter(pk=obj.token_digest).delete()
        obj.delete()

    def delete_queryset(self, request, queryset):
        from knox.models import AuthToken
        AuthToken.objects.filter(pk__in=list(queryset.values_list('token_digest', flat=True))).delete()
        queryset.delete()
    