from django.contrib import admin
from django.contrib.auth import get_user_model
from oauth2_provider.admin import Application, ApplicationAdmin

from janus.models import Profile, ApplicationGroup, ProfilePermission, GroupPermission, ProfileGroup, \
    ApplicationExtension
from django.contrib.auth.admin import UserAdmin



###################################################
# modify the system side admin user view to add an price group

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


# Define a new User admin
# noinspection PyRedeclaration
class UserAdmin(UserAdmin):
    inlines = (ProfileInline,)

    list_display = UserAdmin.list_display + ('profile_groups',)

    def profile_groups(self, obj):
        return obj.profile.get_groups()


# Re-register UserAdmin
admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)

"""
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    list_display_links = ('id', 'user')
    search_fields = ('id', 'user')

admin.site.register(Profile, ProfileAdmin)
"""


class ProfileGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'default')
    list_display_links = ('id', 'name')
    search_fields = ('id', 'name')

admin.site.register(ProfileGroup, ProfileGroupAdmin)


class ApplicationGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('id', 'application', 'name')

admin.site.register(ApplicationGroup, ApplicationGroupAdmin)


class ProfilePermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'application', 'can_authenticate', 'is_superuser',)
    list_display_links = ('id',)
    search_fields = ('id', 'profile', 'application',)

admin.site.register(ProfilePermission, ProfilePermissionAdmin)


class GroupPermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'can_authenticate', 'is_superuser',)
    list_display_links = ('id',)
    search_fields = ('id', 'profile', 'application',)

admin.site.register(GroupPermission, GroupPermissionAdmin)

############################ Application Admin ##################
admin.site.unregister(Application)

class ApplicationExtensionInline(admin.StackedInline):
    model = ApplicationExtension

class ApplicationAdminJanus(ApplicationAdmin):
    list_display = ApplicationAdmin.list_display + ('email_required',)
    inlines = (ApplicationExtensionInline,)

    def email_required(self, object):
        if object.applicationextension:
            return object.applicationextension.email_required
        return None

    email_required.boolean = True


admin.site.register(Application, ApplicationAdminJanus)
