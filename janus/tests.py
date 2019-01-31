import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now
from oauth2_provider.models import Application, AccessToken, Grant

from janus.models import ProfileGroup, Profile, GroupPermission, ProfilePermission, ApplicationGroup
from janus.views import ProfileView

User = get_user_model()


class ProfileGeneration(TestCase):
    def setUp(self):
        user_1 = User.objects.create(username='bob')
        user_group_1 = ProfileGroup.objects.get_or_create(name='default', default=True)
        Profile.create_default_profile(user_1)

    def test_profiles(self):
        all_profiles = Profile.objects.all()
        self.assertEqual(all_profiles.count(), 1)
        bobs_profile = Profile.objects.get(user__username='bob')
        self.assertEqual(bobs_profile.group.all().count(), 1)
        self.assertEqual(bobs_profile.group.first().name, 'default')


class UserAuthenticationTest(TestCase):

    def setUp(self):
        user_group_1 = ProfileGroup.objects.get_or_create(name='secret')
        user_group_2 = ProfileGroup.objects.get_or_create(name='default', default=True)

        user_1 = User.objects.create_user(username='bob', password='testjanus123')
        profile_1 = Profile.objects.create(user=user_1)
        profile_1.group.add(user_group_1[0])
        profile_1.save()

        user_2 = User.objects.create_user(username='alice', password='testjanus123')
        profile_2 = Profile.objects.create(user=user_2)
        profile_2.group.add(user_group_2[0])
        profile_2.save()

        user_3 = User.objects.create_user(username='eve', password='testjanus123')
        profile_3 = Profile.objects.create(user=user_3)
        profile_3.group.add(user_group_2[0])
        profile_3.save()

        app = Application.objects.get_or_create(user=user_1,
                                                redirect_uris='https://localhost:8000/accounts/janus/login/callback/',
                                                client_type='confidential',
                                                authorization_grant_type='authorization-code',
                                                name='test', skip_authorization=True)
        second_app = Application.objects.create(user=user_1,
                                                redirect_uris='https://localhost:8000/accounts/janus/login/callback/',
                                                client_type='confidential',
                                                authorization_grant_type='authorization-code',
                                                name='test_all_superuser', skip_authorization=True)

        gp_1 = GroupPermission.objects.get_or_create(profile_group=user_group_1[0], application=app[0], can_authenticate=True, is_superuser=True)

        gp_1_second_app = GroupPermission.objects.get_or_create(profile_group=user_group_2[0], application=second_app, can_authenticate=True, is_superuser=True)

        gp_2 = GroupPermission.objects.get_or_create(profile_group=user_group_2[0], application=app[0], can_authenticate=True, is_superuser=False)

        ProfilePermission.objects.create(profile=profile_3, application=app[0], is_superuser=True)

        Grant.objects.create(user=user_1, code='abc', application=app[0], expires=now() + timedelta(days=5), redirect_uri='https://localhost:8000/accounts/janus/login/callback/')
        Grant.objects.create(user=user_2, code='abcd', application=app[0], expires=now() + timedelta(days=5), redirect_uri='https://localhost:8000/accounts/janus/login/callback/')
        Grant.objects.create(user=user_3, code='abcde', application=app[0], expires=now() + timedelta(days=5), redirect_uri='https://localhost:8000/accounts/janus/login/callback/')

    def test_not_authenticated(self):
        c = Client()
        response = c.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('hello from janus'.lower(), response.content.decode('utf-8').lower())

    def test_authentication(self):
        response = self.client.login(username='bob', password='testjanus123')
        self.assertTrue(response)

    def test_authentication_2(self):
        c = Client()
        response = c.post(reverse('login'), dict(username='bob', password='testjanus123', response_type='http'))
        response = c.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('hello from janus'.lower(), response.content.decode('utf-8').lower())
        self.assertIn('to bob'.lower(), response.content.decode('utf-8').lower())

    def test_authenticate_bob(self):
        # authenticate the user
        c = Client()
        c.post(reverse('login'), dict(username='bob', password='testjanus123'))

        app = Application.objects.get(name='test')
        token_url = reverse('token')
        response = c.post(token_url, dict(grant_type='authorization_code', code='abc',
                                          client_id=app.client_id, client_secret=app.client_secret,
                                          redirect_uri='https://localhost:8000/accounts/janus/login/callback/'))
        self.assertEqual(response.status_code, 200)
        tokens = json.loads(response.content.decode('utf-8'))

        # get the app settings
        authorize_uri = reverse('authorize')
        response = c.get(authorize_uri, dict(client_id=app.client_id))
        self.assertEqual(response.status_code, 302)

        # get the profile
        profile_uri = reverse('profile')
        response = c.get(profile_uri, dict(access_token=tokens['access_token']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['id'], 'bob')
        self.assertTrue(data['is_superuser'])

    def test_authenticate_alice(self):
        # authenticate the user
        c = Client()
        c.post(reverse('login'), dict(username='alice', password='testjanus123'))

        app = Application.objects.get(name='test')
        token_url = reverse('token')
        response = c.post(token_url, dict(grant_type='authorization_code', code='abcd',
                                          client_id=app.client_id, client_secret=app.client_secret,
                                          redirect_uri='https://localhost:8000/accounts/janus/login/callback/'))
        self.assertEqual(response.status_code, 200)
        tokens = json.loads(response.content.decode('utf-8'))

        # get the app settings
        authorize_uri = reverse('authorize')
        response = c.get(authorize_uri, dict(client_id=app.client_id))
        self.assertEqual(response.status_code, 302)

        # get the profile
        profile_uri = reverse('profile')
        response = c.get(profile_uri, dict(access_token=tokens['access_token']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        print(data)
        self.assertEqual(data['id'], 'alice')
        self.assertFalse(data['is_superuser'])

    def test_authenticate_eve(self):
        # Use eve to see whether profile permissions work
        c = Client()
        c.post(reverse('login'), dict(username='eve', password='testjanus123'))

        app = Application.objects.get(name='test')
        token_url = reverse('token')
        response = c.post(token_url, dict(grant_type='authorization_code', code='abcde',
                                          client_id=app.client_id, client_secret=app.client_secret,
                                          redirect_uri='https://localhost:8000/accounts/janus/login/callback/'))
        self.assertEqual(response.status_code, 200)
        tokens = json.loads(response.content.decode('utf-8'))

        # get the app settings
        authorize_uri = reverse('authorize')
        response = c.get(authorize_uri, dict(client_id=app.client_id))
        self.assertEqual(response.status_code, 302)

        # get the profile
        profile_uri = reverse('profile')
        response = c.get(profile_uri, dict(access_token=tokens['access_token']))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        print(data)
        self.assertEqual(data['id'], 'eve')
        self.assertTrue(data['is_superuser'])




class ProfileViewTests(TestCase):
    def setUp(self):
        # generate some user
        self.user_admin = User.objects.create(username='admin')
        self.user_staff = User.objects.create(username='help-desk-user')
        self.user_customer = User.objects.create(username='customer')

        # init some profile groups
        self.group_default = ProfileGroup.objects.create(name='default', default=True)
        self.group_superuser = ProfileGroup.objects.create(name='superuser_group')
        self.group_staff = ProfileGroup.objects.create(name='staff_group')
        self.group_customer = ProfileGroup.objects.create(name='customer_group')

        # init user profiles
        Profile.create_default_profile(self.user_admin)
        Profile.create_default_profile(self.user_staff)
        Profile.create_default_profile(self.user_customer)

        # some apps
        self.application_one = Application.objects.create(user=None,
                                                redirect_uris='https://localhost:8000/accounts/janus/login/callback/',
                                                client_type='confidential',
                                                authorization_grant_type='authorization-code',
                                                name='test', skip_authorization=True)
        self.application_two = Application.objects.create(user=None,
                                                redirect_uris='https://localhost:8000/accounts/janus/login/callback/',
                                                client_type='confidential',
                                                authorization_grant_type='authorization-code',
                                                name='test_all_superuser', skip_authorization=True)

        # generate some application groups (the groups will be returned to the app on profile call)
        staff_app_group = ApplicationGroup.objects.create(application=self.application_one,
                                                                 name="django_user_staff",
                                                                 description="staff")
        customer_app_group = ApplicationGroup.objects.create(application=self.application_one,
                                                                    name="django_customer",
                                                                    description="customer")

        app2_group1 = ApplicationGroup.objects.create(application=self.application_two,
                                                                    name="group1")
        app2_group2 = ApplicationGroup.objects.create(application=self.application_two,
                                                                            name="group2")
        app2_group3 = ApplicationGroup.objects.create(application=self.application_one,
                                                                            name="group3")

        # add app_groups to profile_groups iva (profile)group permissions
        gp1 = GroupPermission.objects.create(profile_group=self.group_staff, application=self.application_one)
        gp1.groups.add(staff_app_group)

        gp2 = GroupPermission.objects.create(profile_group=self.group_staff, application=self.application_one)
        gp2.groups.add(customer_app_group)


        gp2 = GroupPermission.objects.create(profile_group=self.group_superuser, application=self.application_two)
        gp2.groups.add(app2_group1, app2_group2, app2_group3) # group3 is not supposed in here, simulate human error



    def test_profile_view_groups(self):
        # check ProfileView
        pv = ProfileView()

        # add users to groups
        self.user_staff.profile.group.add(self.group_staff)
        self.user_staff.profile.group.add(self.group_customer)

        list_group_names = pv.get_profile_group_memberships(self.user_staff, self.application_one)
        self.assertIn("django_user_staff", list_group_names)
        self.assertIn("django_customer", list_group_names)


        list_empty_groups = pv.get_profile_group_memberships(self.user_customer, self.application_one)
        self.assertAlmostEqual(len(list_empty_groups), 0)


        # test super user has on app2 -> group1, group2
        self.user_admin.profile.group.add(self.group_superuser)
        list_two_not_three = pv.get_profile_group_memberships(self.user_admin, self.application_two)
        self.assertIn("group1", list_two_not_three)
        self.assertIn("group2", list_two_not_three)
        self.assertNotIn("group3", list_two_not_three)
        # also group3 is only linked to the wrong app so its also not present in the desired app
        list_empty_again = pv.get_profile_group_memberships(self.user_admin, self.application_one)
        self.assertAlmostEqual(len(list_empty_again), 0)




