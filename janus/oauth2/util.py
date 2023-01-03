from janus.models import ProfileGroup, Profile, GroupPermission, ProfilePermission


def get_profile_memberships(user):
    all_profiles = Profile.objects.get(user=user).group.all()

    # add the default groups by default
    default_profile = ProfileGroup.objects.filter(default=True)
    all_profiles = set(all_profiles | default_profile)

    return list(all_profiles)


def get_group_permissions(user, application):
    """
    Validates the group permissions for a user given a token
    :param user:
    :param token:
    :return:
    """
    is_staff = False
    is_superuser = False
    can_authenticate = False

    if not user.is_authenticated:
        return can_authenticate, is_staff, is_superuser

    all_groups = get_profile_memberships(user)

    for g in all_groups:
        gp = GroupPermission.objects.filter(profile_group=g, application=application)
        if gp.count() == 0:
            continue
        elif gp.count() == 1:
            gp = gp.first()
            if gp.can_authenticate:
                can_authenticate = True
            if gp.is_staff:
                is_staff = True
            if gp.is_superuser:
                is_superuser = True
        else:
            print('We have a problem')
    return can_authenticate, is_staff, is_superuser


def get_personal_permissions(user, application):
    """
    Validates the personal permissions for a user given a token
    :param user:
    :param token:
    :return:
    """
    is_staff = None
    is_superuser = None
    can_authenticate = None
    if not user.is_authenticated:
        return can_authenticate, is_staff, is_superuser

    pp = ProfilePermission.objects.filter(profile__user=user, application=application).first()
    if pp:
        is_staff = True if pp.is_staff else None
        is_superuser = True if pp.is_superuser else None
        can_authenticate = True if pp.can_authenticate else None
    return can_authenticate, is_staff, is_superuser


def get_profile_group_memberships(user, application):
    """
    collect group names form user profile group memberships
    :param user:
    :param token:
    :return:
    """

    all_profiles = get_profile_memberships(user)

    group_list = set()

    for g in all_profiles:
        # get profile-group-permission object
        gp = GroupPermission.objects.filter(profile_group=g, application=application)
        for elem in gp:
            groups = elem.groups.all()

            for g in groups:
                # ensure only groups for this application can be returned
                if g.application == application:
                    group_list.add(g.name)

    return group_list


def get_profile_personal_memberships(user, application):
    """
    collect group names form user profile permission
    :param user:
    :param token:
    :return:
    """

    profile_permissions = ProfilePermission.objects.filter(profile__user=user, application=application).first()

    group_list = set()

    if profile_permissions:
        groups = profile_permissions.groups.all()

        for g in groups:
            # ensure only groups for this application can be returned
            if g.application == application:
                group_list.add(g.name)

    return group_list


def get_permissions(user, application):
    """
    return permissions according to application settings, personal overwrite and default values
    :param user:
    :param application:
    :return:
    """
    can_authenticate, is_staff, is_superuser = get_group_permissions(user, application)

    # if set the personal settings overwrite the user settings
    pp_authenticate, pp_staff, pp_superuser = get_personal_permissions(user, application)
    if pp_staff is not None:
        is_staff = pp_staff

    if pp_superuser is not None:
        is_superuser = pp_superuser

    if pp_authenticate is not None:
        can_authenticate = pp_authenticate

    return can_authenticate, is_staff, is_superuser


def get_group_list(user, application):
    groups = set()
    groups = groups.union(get_profile_group_memberships(user, application))
    groups = groups.union(get_profile_personal_memberships(user, application))

    return list(groups)
