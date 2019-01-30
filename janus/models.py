from django.db import models
from django.contrib.auth.models import User
from oauth2_provider.models import Application


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ManyToManyField('ProfileGroup', blank=True)

    def get_groups(self):
        ret = ""
        for g in self.group.all():
            if ret != "":
                ret += ", "
            ret += str(g)
        return ret

    def __str__(self):
        return self.user.username

    @staticmethod
    def create_default_profile(user):
        p = Profile()
        p.user = user
        p.save()

        default_groups = ProfileGroup.objects.filter(default=True).all()
        if default_groups.exists():
            p.group.add(default_groups)

        p.save()


class ProfileGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ApplicationGroup(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    # the name will be returned as char to the application
    name = models.CharField(max_length=255)
    description = models.TextField(default="")

    def __str__(self):
        return self.name


class ProfilePermission(models.Model):
    class Meta:
        unique_together = (('profile', 'application', ), )

    """ override all permissions for a single application """
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    # this defines if the oauth module issues an authentication token
    can_authenticate = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(ApplicationGroup, blank=True)


class GroupPermission(models.Model):
    """ 
        define default permissions for applications, can be overridden by a entry in the ApplicationPermission model
        additive override for the bool values
    """
    profile_group = models.ForeignKey(ProfileGroup, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    can_authenticate = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    # group also work additive, if the profile is in multiple groups, we collect alle the groups and return them
    # the application must deal with inconsistency
    groups = models.ManyToManyField(ApplicationGroup, blank=True,)


class ApplicationExtension(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE)
    email_required = models.BooleanField(default=False)
    display_name = models.CharField(max_length=255, null=True, blank=True, default=None)
    link = models.URLField(default=None, blank=True, null=True)
