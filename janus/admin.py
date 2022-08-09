import json

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.template import Template
from django.utils.module_loading import import_string
from fakeinline.datastructures import FakeFormSet, FakeInline, FakeForm
from oauth2_provider.admin import Application, ApplicationAdmin

from janus.app_settings import ALLAUTH_JANUS_ADMIN_CLASS
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


###### extent admin for easy user debug

class FakeFormNew(FakeForm):
    def is_multipart(self):
        return False

class FakeFormSetNew(FakeFormSet):
    form = FakeFormNew
    empty_form = FakeFormNew

class ApplicationGroupFormSet(FakeFormSetNew):
    # this probably works, but usually you'd point it at a template file.
    template = Template('''
    <p>Debug applied application groups (save to see the update!):
    {% for key, value in inline_admin_formset.formset.get_applications.items %}
    <p>applicatio "{{ key }}":<br/>
    {{ value }}
    </p>
    {% endfor %}
    
    
    </p>
    ''')

    def is_multipart(self):
        return False


    def get_applications(self):
        user = self.instance

        from janus.views import ProfileView
        pv = ProfileView()

        ret = {}

        from oauth2_provider.models import Application as Application2

        applications = Application2.objects.all()

        for application in applications:
            ret[application.name] = pv.get_group_list(user, application)

        return ret


class ApplicationGroups(FakeInline):
    formset = ApplicationGroupFormSet


# Define a new User admin
# noinspection PyRedeclaration
class JanusUserAdmin(UserAdmin):
    inlines = (ProfileInline, ApplicationGroups)

    list_display = UserAdmin.list_display + ('profile_groups',)

    def profile_groups(self, obj):
        return obj.profile.get_groups()


# Re-register UserAdmin
admin.site.unregister(get_user_model())

# overwrite admin class if user wants to
JanusUserAdminClass = import_string(ALLAUTH_JANUS_ADMIN_CLASS)
admin.site.register(get_user_model(), JanusUserAdminClass)

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
    list_display = ('id', 'profile', 'application', 'can_authenticate', 'is_staff', 'is_superuser',)
    list_display_links = ('id',)
    search_fields = ('id', 'profile', 'application',)

admin.site.register(ProfilePermission, ProfilePermissionAdmin)


class GroupPermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile_group', 'application', 'can_authenticate', 'is_staff', 'is_superuser',)
    list_display_links = ('id',)
    search_fields = ('id', 'profile_group', 'application',)

admin.site.register(GroupPermission, GroupPermissionAdmin)

############################ Application Admin ##################
admin.site.unregister(Application)

class ApplicationExtensionInline(admin.StackedInline):
    model = ApplicationExtension

class ApplicationAdminJanus(ApplicationAdmin):
    list_display = ApplicationAdmin.list_display + ('email_required',)
    inlines = (ApplicationExtensionInline,)

    def email_required(self, object):
        if object.extension:
            return object.extension.email_required
        return None

    email_required.boolean = True


admin.site.register(Application, ApplicationAdminJanus)
