from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.http import Http404, HttpResponse
import json
import httplib
import owncloud
import requests
import mock
from nose import tools as nt

from admin_tests.utilities import setup_user_view
from admin.rdm_custom_storage_location import views
from addons.osfstorage.models import Region
from tests.base import AdminTestCase
from osf_tests.factories import (
    AuthUserFactory,
    RegionFactory,
    InstitutionFactory,
)
from django.utils import timezone
from osf.models.external import ExternalAccount, ExternalAccountTemporary


class TestInstitutionDefaultStorage(AdminTestCase):
    def setUp(self):
        super(TestInstitutionDefaultStorage, self).setUp()
        self.institution1 = InstitutionFactory()
        self.institution2 = InstitutionFactory()
        self.user = AuthUserFactory()
        self.default_region = Region.objects.first()

        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution1)
        self.user.save()
        self.request = RequestFactory().get('/fake_path')
        self.view = views.InstitutionalStorage()
        self.view = setup_user_view(self.view, self.request, user=self.user)
        self.addon_type_dict = [
            'BoxAddonAppConfig',
            'OSFStorageAddonAppConfig',
            'OwnCloudAddonAppConfig',
            'S3AddonAppConfig',
            'GoogleDriveAddonConfig',
            'SwiftAddonAppConfig',
            'S3CompatAddonAppConfig',
            'NextcloudAddonAppConfig',
        ]

    def test_admin_login(self):
        self.request.user.is_active = True
        self.request.user.is_registered = True
        self.request.user.is_superuser = False
        self.request.user.is_staff = True
        nt.assert_true(self.view.test_func())

    def test_get(self, *args, **kwargs):
        res = self.view.get(self.request, *args, **kwargs)
        nt.assert_equal(res.status_code, 200)

    def test_get_without_custom_storage(self, *args, **kwargs):
        res = self.view.get(self.request, *args, **kwargs)
        for addon in res.context_data['providers']:
            nt.assert_true(type(addon).__name__ in self.addon_type_dict)
        nt.assert_equal(res.context_data['region'], self.default_region)
        nt.assert_equal(res.context_data['selected_provider_short_name'], 'osfstorage')

    def test_get_custom_storage(self, *args, **kwargs):
        self.us = RegionFactory()
        self.us._id = self.institution1._id
        self.us.save()
        res = self.view.get(self.request, *args, **kwargs)
        for addon in res.context_data['providers']:
            nt.assert_true(type(addon).__name__ in self.addon_type_dict)
        nt.assert_equal(res.context_data['region'], self.us)
        nt.assert_equal(res.context_data['selected_provider_short_name'], res.context_data['region'].waterbutler_settings['storage']['provider'])


class TestIconView(AdminTestCase):
    def setUp(self):
        super(TestIconView, self).setUp()
        self.user = AuthUserFactory()
        self.request = RequestFactory().get('/fake_path')
        self.view = views.IconView()
        self.view = setup_user_view(self.view, self.request, user=self.user)

    def tearDown(self):
        super(TestIconView, self).tearDown()
        self.user.delete()

    def test_login_user(self):
        nt.assert_true(self.view.test_func())

    def test_valid_get(self, *args, **kwargs):
        self.view.kwargs = {'addon_name': 's3'}
        res = self.view.get(self.request, *args, **self.view.kwargs)
        nt.assert_equal(res.status_code, 200)

    def test_invalid_get(self, *args, **kwargs):
        self.view.kwargs = {'addon_name': 'invalidprovider'}
        with nt.assert_raises(Http404):
            self.view.get(self.request, *args, **self.view.kwargs)


class TestPermissionTestConnection(AdminTestCase):

    def setUp(self):
        self.user = AuthUserFactory()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.test_connection(request)

    def test_normal_user(self):
        with self.assertRaises(PermissionDenied):
            self.view_post({})

    def test_staff_without_institution(self):
        self.user.is_staff = True
        self.user.save()

        with self.assertRaises(PermissionDenied):
            self.view_post({})

    def test_staff_with_institution(self):
        institution = InstitutionFactory()

        self.user.is_staff = True
        self.user.affiliated_institutions.add(institution)
        self.user.save()

        response = self.view_post({})
        nt.assert_is_instance(response, HttpResponse)

    def test_superuser(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        with self.assertRaises(PermissionDenied):
            self.view_post({})


class TestPermissionSaveCredentials(AdminTestCase):

    def setUp(self):
        self.user = AuthUserFactory()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    def test_normal_user(self):
        with self.assertRaises(PermissionDenied):
            self.view_post({})

    def test_staff_without_institution(self):
        self.user.is_staff = True
        self.user.save()

        with self.assertRaises(PermissionDenied):
            self.view_post({})

    def test_staff_with_institution(self):
        institution = InstitutionFactory()

        self.user.is_staff = True
        self.user.affiliated_institutions.add(institution)
        self.user.save()

        response = self.view_post({})
        nt.assert_is_instance(response, HttpResponse)

    def test_superuser(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        with self.assertRaises(PermissionDenied):
            self.view_post({})


class TestPermissionFetchTemporaryToken(AdminTestCase):

    def setUp(self):
        self.user = AuthUserFactory()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.fetch_temporary_token(request)

    def test_normal_user(self):
        with self.assertRaises(PermissionDenied):
            self.view_post({})

    def test_staff_without_institution(self):
        self.user.is_staff = True
        self.user.save()

        with self.assertRaises(PermissionDenied):
            self.view_post({})

    def test_staff_with_institution(self):
        institution = InstitutionFactory()

        self.user.is_staff = True
        self.user.affiliated_institutions.add(institution)
        self.user.save()

        response = self.view_post({})
        nt.assert_is_instance(response, HttpResponse)

    def test_superuser(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        with self.assertRaises(PermissionDenied):
            self.view_post({})


class TestS3ConnectionStorage(AdminTestCase):

    def setUp(self):
        super(TestS3ConnectionStorage, self).setUp()
        self.mock_can_list = mock.patch('addons.s3.views.utils.can_list')
        self.mock_can_list.return_value = True
        self.mock_can_list.start()

        config = {
            'return_value.id': '12346789',
            'return_value.display_name': 's3.user',
            'return_value.Owner': 'Owner',
        }
        self.mock_uid = mock.patch('addons.s3.views.utils.get_user_info', **config)
        self.mock_uid.start()
        self.mock_exists = mock.patch('addons.s3.views.utils.bucket_exists')
        self.mock_exists.return_value = True
        self.mock_exists.start()

        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.test_connection(request)

    def test_without_provider(self):
        params = {
            's3_access_key': '',
            's3_secret_key': ''
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', request_post_response.content)

    def test_s3_settings_input_empty_keys(self):
        params = {
            's3_access_key': '',
            's3_secret_key': '',
            'provider_short_name': '',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', request_post_response.content)

    def test_s3_settings_input_invalid_provider(self):
        params = {
            's3_access_key': '',
            's3_secret_key': '',
            'provider_short_name': 'invalidprovider',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Invalid provider.', request_post_response.content)

    def test_s3_settings_input_empty_keys_with_provider(self):
        params = {
            's3_access_key': '',
            's3_secret_key': '',
            'provider_short_name': 's3',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('All the fields above are required.', request_post_response.content)

    def test_s3_settings_input_empty_access_key(self):
        params = {
            's3_access_key': '',
            's3_secret_key': 'Non-empty-secret-key',
            'provider_short_name': 's3',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('All the fields above are required.', request_post_response.content)

    def test_s3_settings_input_empty_secret_key(self):
        params = {
            's3_access_key': 'Non-empty-secret-key',
            's3_secret_key': '',
            'provider_short_name': 's3',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('All the fields above are required.', request_post_response.content)

    @mock.patch('addons.s3.views.utils.can_list', return_value=False)
    def test_user_settings_cant_list(self, mock_can_list):
        params = {
            's3_access_key': 'Non-empty-secret-key',
            's3_secret_key': 'Non-empty-secret-key',
            'provider_short_name': 's3',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Unable to list buckets.', request_post_response.content)

    @mock.patch('addons.s3.views.utils.can_list', return_value=True)
    def test_user_settings_can_list(self, mock_can_list):
        params = {
            's3_access_key': 'Non-empty-secret-key',
            's3_secret_key': 'Non-empty-secret-key',
            'provider_short_name': 's3',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.OK)
        nt.assert_in('Credentials are valid', request_post_response.content)

    @mock.patch('addons.s3.views.utils.get_user_info', return_value=None)
    def test_user_settings_invalid_credentials(self, mock_uid):
        params = {
            's3_access_key': 'Non-empty-secret-key',
            's3_secret_key': 'Non-empty-secret-key',
            'provider_short_name': 's3',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Unable to access account.\\n'
                'Check to make sure that the above credentials are valid,'
                'and that they have permission to list buckets.', request_post_response.content)


class TestOwncloudConnectionStorage(AdminTestCase):

    def setUp(self):
        super(TestOwncloudConnectionStorage, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.test_connection(request)

    @mock.patch('owncloud.Client')
    def test_success_owncloud(self, mock_client):
        response = self.view_post({
            'owncloud_host': 'my-valid-host',
            'owncloud_username': 'my-valid-username',
            'owncloud_password': 'my-valid-password',
            'owncloud_folder': 'my-valid-folder',
            'provider_short_name': 'owncloud',
        })
        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('Credentials are valid', response.content)

    @mock.patch('owncloud.Client')
    def test_success_nextcloud(self, mock_client):
        response = self.view_post({
            'nextcloud_host': 'my-valid-host',
            'nextcloud_username': 'my-valid-username',
            'nextcloud_password': 'my-valid-password',
            'nextcloud_folder': 'my-valid-folder',
            'provider_short_name': 'nextcloud',
        })
        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('Credentials are valid', response.content)

    @mock.patch('owncloud.Client')
    def test_connection_error(self, mock_client):
        mock_client.side_effect = requests.exceptions.ConnectionError()

        response = self.view_post({
            'owncloud_host': 'cuzidontcare',
            'owncloud_username': 'my-valid-username',
            'owncloud_password': 'my-valid-password',
            'owncloud_folder': 'my-valid-folder',
            'provider_short_name': 'owncloud',
        })
        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Invalid ownCloud server.', response.content)

    @mock.patch('owncloud.Client')
    def test_unauthorized(self, mock_client):
        res = HttpResponse(status=httplib.UNAUTHORIZED)
        mock_client.side_effect = owncloud.owncloud.HTTPResponseError(res)

        response = self.view_post({
            'owncloud_host': 'my-valid-host',
            'owncloud_username': 'bad-username',
            'owncloud_password': 'bad-password',
            'owncloud_folder': 'my-valid-folder',
            'provider_short_name': 'owncloud',
        })
        nt.assert_equals(response.status_code, httplib.UNAUTHORIZED)
        nt.assert_in('ownCloud Login failed.', response.content)

class TestSwiftConnectionStorage(AdminTestCase):

    def setUp(self):
        super(TestSwiftConnectionStorage, self).setUp()
        self.mock_can_list = mock.patch('addons.swift.views.utils.can_list')
        self.mock_can_list.return_value = True
        self.mock_can_list.start()

        self.mock_uid = mock.patch('addons.swift.views.utils.get_user_info')
        self.mock_uid.return_value = {'id': '1234567890', 'display_name': 'swift.user'}
        self.mock_uid.start()

        config = {
            'return_value.id': '12346789',
            'return_value.display_name': 'swift.user',
        }
        self.mock_exists = mock.patch('addons.swift.views.utils.container_exists', **config)
        self.mock_exists.return_value = True
        self.mock_exists.start()

        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def tearDown(self):
        self.mock_can_list.stop()
        self.mock_uid.stop()
        self.mock_exists.stop()
        super(TestSwiftConnectionStorage, self).tearDown()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.test_connection(request)

    def test_swift_settings_input_empty_keys(self):
        params = {
            'swift_auth_version': '',
            'swift_auth_url': '',
            'swift_access_key': '',
            'swift_secret_key': '',
            'swift_tenant_name': '',
            'swift_folder': '',
            'swift_container': '',
            'provider_short_name': 'swift',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('All the fields above are required.', request_post_response.content)

    def test_swift_settings_input_empty_swift_user_domain_name_v3(self):
        params = {
            'swift_auth_version': '3',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_access_key': 'Non-empty-access-key',
            'swift_secret_key': 'Non-empty-secret-key',
            'swift_tenant_name': 'Non-empty-tenant_name',
            'swift_user_domain_name': '',
            'swift_project_domain_name': 'Non-empty-project_domain_name',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('The field `user_domain_name` is required when you choose identity V3.', request_post_response.content)

    def test_swift_settings_input_empty_swift_project_domain_name_v3(self):
        params = {
            'swift_auth_version': '3',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_access_key': 'Non-empty-access-key',
            'swift_secret_key': 'Non-empty-secret-key',
            'swift_tenant_name': 'Non-empty-tenant_name',
            'swift_user_domain_name': 'Non-empty-user_domain_name',
            'swift_project_domain_name': '',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('The field `project_domain_name` is required when you choose identity V3.', request_post_response.content)

    @mock.patch('addons.swift.views.utils.get_user_info', return_value=None)
    def test_swift_settings_invalid_credentials(self, mock_uid):
        params = {
            'swift_auth_version': '3',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_access_key': 'Non-empty-access-key',
            'swift_secret_key': 'Non-empty-secret-key',
            'swift_tenant_name': 'Non-empty-tenant_name',
            'swift_user_domain_name': 'Non-empty-user_domain_name',
            'swift_project_domain_name': 'Non-empty-project_domain_name',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Unable to access account.\\n'
                'Check to make sure that the above credentials are valid, '
                'and that they have permission to list containers.', request_post_response.content)

    @mock.patch('addons.swift.views.utils.can_list', return_value=False)
    def test_swift_settings_cant_list_v3(self, mock_can_list):
        params = {
            'swift_auth_version': '3',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_access_key': 'Non-empty-access-key',
            'swift_secret_key': 'Non-empty-secret-key',
            'swift_tenant_name': 'Non-empty-tenant_name',
            'swift_user_domain_name': 'Non-empty-user_domain_name',
            'swift_project_domain_name': 'Non-empty-project_domain_name',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Unable to list containers.\\n'
                'Listing containers is required permission.', request_post_response.content)

    def test_swift_settings_can_list_v3(self):
        params = {
            'swift_auth_version': '3',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_access_key': 'Non-empty-access-key',
            'swift_secret_key': 'Non-empty-secret-key',
            'swift_tenant_name': 'Non-empty-tenant_name',
            'swift_user_domain_name': 'Non-empty-user_domain_name',
            'swift_project_domain_name': 'Non-empty-project_domain_name',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        }
        request_post_response = self.view_post(params)
        nt.assert_equals(request_post_response.status_code, httplib.OK)
        nt.assert_in('Credentials are valid', request_post_response.content)


class TestS3SaveCredentials(AdminTestCase):

    def setUp(self):
        super(TestS3SaveCredentials, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    def test_provider_missing(self):
        response = self.view_post({
            'storage_name': 'My storage',
            's3_access_key': 'Non-empty-access-key',
            's3_secret_key': 'Non-empty-secret-key',
            's3_bucket': 'Cute bucket',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_invalid_provider(self):
        response = self.view_post({
            'storage_name': 'My storage',
            's3_access_key': 'Non-empty-access-key',
            's3_secret_key': 'Non-empty-secret-key',
            's3_bucket': 'Cute bucket',
            'provider_short_name': 'invalidprovider',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Invalid provider.', response.content)

    @mock.patch('admin.rdm_custom_storage_location.utils.test_s3_connection')
    def test_success(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'Nice'}, httplib.OK
        response = self.view_post({
            'storage_name': 'My storage',
            's3_access_key': 'Non-empty-access-key',
            's3_secret_key': 'Non-empty-secret-key',
            's3_bucket': 'Cute bucket',
            'provider_short_name': 's3',
        })

        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('Saved credentials successfully!!', response.content)

        institution_storage = Region.objects.filter(_id=self.institution._id).first()
        nt.assert_is_not_none(institution_storage)
        nt.assert_equals(institution_storage.name, 'My storage')

        wb_credentials = institution_storage.waterbutler_credentials
        nt.assert_equals(wb_credentials['storage']['access_key'], 'Non-empty-access-key')
        nt.assert_equals(wb_credentials['storage']['secret_key'], 'Non-empty-secret-key')

        wb_settings = institution_storage.waterbutler_settings
        nt.assert_equals(wb_settings['storage']['provider'], 's3')
        nt.assert_equals(wb_settings['storage']['bucket'], 'Cute bucket')

    @mock.patch('admin.rdm_custom_storage_location.utils.test_s3_connection')
    def test_invalid_credentials(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'NG'}, httplib.BAD_REQUEST

        response = self.view_post({
            'storage_name': 'My storage',
            's3_access_key': 'Wrong-access-key',
            's3_secret_key': 'Wrong-secret-key',
            's3_bucket': 'Cute bucket',
            'provider_short_name': 's3',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('NG', response.content)
        nt.assert_false(Region.objects.filter(_id=self.institution._id).exists())

class TestSwiftSaveCredentials(AdminTestCase):

    def setUp(self):
        super(TestSwiftSaveCredentials, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    def test_provider_missing(self):
        response = self.view_post({
            'storage_name': 'Rando Randerson\'s storage',
            'auth_version': '3 I guess?',
            'access_key': 'Non-empty-access-key',
            'secret_key': 'Non-empty-secret-key',
            'tenant_name': 'Non-empty-tenant-name',
            'user_domain_name': 'Non-empty-user-domain-name',
            'project_domain_name': 'Non-empty-project-domain-name',
            'auth_url': 'Non-empty-auth-url',
            'folder': 'Non-empty-folder',
            'container': 'Non-empty-container',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_invalid_provider(self):
        response = self.view_post({
            'storage_name': 'Rando Randerson\'s storage',
            'auth_version': '3 I guess?',
            'access_key': 'Non-empty-access-key',
            'secret_key': 'Non-empty-secret-key',
            'tenant_name': 'Non-empty-tenant-name',
            'user_domain_name': 'Non-empty-user-domain-name',
            'project_domain_name': 'Non-empty-project-domain-name',
            'auth_url': 'Non-empty-auth-url',
            'folder': 'Non-empty-folder',
            'container': 'Non-empty-container',
            'provider_short_name': 'invalidprovider',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Invalid provider.', response.content)

    @mock.patch('admin.rdm_custom_storage_location.utils.test_swift_connection')
    def test_success(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'Nice'}, httplib.OK
        response = self.view_post({
            'storage_name': 'My storage',
            'swift_auth_version': '3 I guess?',
            'swift_access_key': 'Non-empty-access-key',
            'swift_secret_key': 'Non-empty-secret-key',
            'swift_tenant_name': 'Non-empty-tenant-name',
            'swift_user_domain_name': 'Non-empty-user-domain-name',
            'swift_project_domain_name': 'Non-empty-project-domain-name',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        })

        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('Saved credentials successfully!!', response.content)

        institution_storage = Region.objects.filter(_id=self.institution._id).first()
        nt.assert_is_not_none(institution_storage)
        nt.assert_equals(institution_storage.name, 'My storage')

        wb_credentials = institution_storage.waterbutler_credentials
        nt.assert_equals(wb_credentials['storage']['username'], 'Non-empty-access-key')
        nt.assert_equals(wb_credentials['storage']['password'], 'Non-empty-secret-key')

        wb_settings = institution_storage.waterbutler_settings
        nt.assert_equals(wb_settings['storage']['provider'], 'swift')
        nt.assert_equals(wb_settings['storage']['container'], 'Non-empty-container')

    @mock.patch('admin.rdm_custom_storage_location.utils.test_swift_connection')
    def test_invalid_credentials(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'NG'}, httplib.BAD_REQUEST

        response = self.view_post({
            'storage_name': 'My storage',
            'swift_auth_version': '3 I guess?',
            'swift_access_key': 'Wrong access key',
            'swift_secret_key': 'Wrong secret key',
            'swift_tenant_name': 'Non-empty-tenant-name',
            'swift_user_domain_name': 'Non-empty-user-domain-name',
            'swift_project_domain_name': 'Non-empty-project-domain-name',
            'swift_auth_url': 'Non-empty-auth-url',
            'swift_folder': 'Non-empty-folder',
            'swift_container': 'Non-empty-container',
            'provider_short_name': 'swift',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('NG', response.content)
        nt.assert_false(Region.objects.filter(_id=self.institution._id).exists())

class TestGoogleDriveConnectionTest(AdminTestCase):
    def setUp(self):
        super(TestGoogleDriveConnectionTest, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()
        self.seed_data = {
            'provider_name': 'googledrive',
            'oauth_key': 'pzN7NJr1EDzXDHsoZRqJT6jHVkt7ryhQbOzQjiduLmPw8CHs8lzrUBrBiztMQvxK5KLplhpKuGxeP91W',
            'oauth_secret': 'qgKnksgBkx76yCl9CqtTP4DOzPYiHLN9LSHFoVsgLgCc6ZqXngWMww5ydxrqY6OzyjUAcP5wL8c58D1Z',
            'expires_at': timezone.now(),
            'refresh_token': 'e97DkIMV6B0j6NjD1CYIiAm4',
            'date_last_refreshed': timezone.now(),
            'display_name': 'google drive display name is here',
            'profile_url': 'example.com',
            '_id': self.institution._id,
            'provider_id': '88080800880',
        }

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.fetch_temporary_token(request)

    def test_provider_missing(self):
        response = self.view_post({
            'no_pro': 'googledrive',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_fail_Oauth_procedure_canceled(self):
        response = self.view_post({
            'provider_short_name': 'googledrive',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Oauth permission procedure was canceled', response.content)

    def test_success(self):
        temp_account = ExternalAccountTemporary.objects.create(
            provider=self.seed_data['provider_name'],
            provider_name=self.seed_data['provider_name'],
            oauth_key=self.seed_data['oauth_key'],
            oauth_secret=self.seed_data['oauth_secret'],
            expires_at=self.seed_data['expires_at'],
            refresh_token=self.seed_data['refresh_token'],
            date_last_refreshed=self.seed_data['date_last_refreshed'],
            display_name=self.seed_data['display_name'],
            profile_url=self.seed_data['profile_url'],
            _id=self.seed_data['_id'],
            provider_id=self.seed_data['provider_id'],
        )
        response = self.view_post({
            'provider_short_name': 'googledrive',
        })
        nt.assert_equals(response.status_code, httplib.OK)
        data = json.loads(response.content)
        response_temp_account = data['response_data']
        nt.assert_equals(response_temp_account['display_name'], temp_account.display_name)
        nt.assert_equals(response_temp_account['oauth_key'], temp_account.oauth_key)
        nt.assert_equals(response_temp_account['provider'], temp_account.provider)
        nt.assert_equals(response_temp_account['provider_id'], temp_account.provider_id)
        nt.assert_equals(response_temp_account['provider_name'], temp_account.provider_name)
        nt.assert_equals(response_temp_account['fullname'], self.user.fullname)

class TestBoxConnectionTest(AdminTestCase):
    def setUp(self):
        super(TestBoxConnectionTest, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()
        self.seed_data = {
            'provider_name': 'box',
            'oauth_key': 'pzN7NJr1EDzXDHsoZRqJT6jHVkt7ryhQbOzQjiduLmPw8CHs8lzrUBrBiztMQvxK5KLplhpKuGxeP91W',
            'oauth_secret': 'qgKnksgBkx76yCl9CqtTP4DOzPYiHLN9LSHFoVsgLgCc6ZqXngWMww5ydxrqY6OzyjUAcP5wL8c58D1Z',
            'expires_at': timezone.now(),
            'refresh_token': 'e97DkIMV6B0j6NjD1CYIiAm4',
            'date_last_refreshed': timezone.now(),
            'display_name': 'box display name is here',
            'profile_url': 'example.com',
            '_id': self.institution._id,
            'provider_id': '88080800880',
        }

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.fetch_temporary_token(request)

    def test_provider_missing(self):
        response = self.view_post({
            'no_pro': 'box',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_fail_Oauth_procedure_canceled(self):
        response = self.view_post({
            'provider_short_name': 'box',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Oauth permission procedure was canceled', response.content)

    def test_success(self):
        temp_account = ExternalAccountTemporary.objects.create(
            provider=self.seed_data['provider_name'],
            provider_name=self.seed_data['provider_name'],
            oauth_key=self.seed_data['oauth_key'],
            oauth_secret=self.seed_data['oauth_secret'],
            expires_at=self.seed_data['expires_at'],
            refresh_token=self.seed_data['refresh_token'],
            date_last_refreshed=self.seed_data['date_last_refreshed'],
            display_name=self.seed_data['display_name'],
            profile_url=self.seed_data['profile_url'],
            _id=self.seed_data['_id'],
            provider_id=self.seed_data['provider_id'],
        )
        response = self.view_post({
            'provider_short_name': 'box',
        })
        nt.assert_equals(response.status_code, httplib.OK)
        data = json.loads(response.content)
        response_temp_account = data['response_data']
        nt.assert_equals(response_temp_account['display_name'], temp_account.display_name)
        nt.assert_equals(response_temp_account['oauth_key'], temp_account.oauth_key)
        nt.assert_equals(response_temp_account['provider'], temp_account.provider)
        nt.assert_equals(response_temp_account['provider_id'], temp_account.provider_id)
        nt.assert_equals(response_temp_account['provider_name'], temp_account.provider_name)
        nt.assert_equals(response_temp_account['fullname'], self.user.fullname)

class TestNiiStorageTest(AdminTestCase):
    def setUp(self):
        super(TestNiiStorageTest, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    def test_provider_missing(self):
        response = self.view_post({
            'no_pro': 'osfstorage',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_success(self):
        response = self.view_post({
            'provider_short_name': 'osfstorage',
        })

        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('NII storage was set successfully', response.content)


class TestOwnCloudStorageSaveCredentials(AdminTestCase):
    def setUp(self):
        super(TestOwnCloudStorageSaveCredentials, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    @mock.patch('admin.rdm_custom_storage_location.utils.test_owncloud_connection')
    def test_connection_fail(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'NG'}, httplib.BAD_REQUEST

        response = self.view_post({
            'storage_name': 'My storage',
            'owncloud_host': 'drop database;',
            'owncloud_username': 'invalid-user',
            'owncloud_password': 'invalid-password',
            'owncloud_folder': 'Hello World',
            'provider_short_name': 'owncloud',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('NG', response.content)
        nt.assert_false(Region.objects.filter(_id=self.institution._id).exists())

    @mock.patch('admin.rdm_custom_storage_location.utils.test_owncloud_connection')
    def test_success(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'Nice'}, httplib.OK

        response = self.view_post({
            'storage_name': 'My storage',
            'owncloud_host': 'valid.owncloud.net',
            'owncloud_username': 'admin',
            'owncloud_password': '1234',
            'owncloud_folder': 'reserved_for_osf',
            'provider_short_name': 'owncloud',
        })

        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('Saved credentials successfully!!', response.content)

        institution_storage = Region.objects.filter(_id=self.institution._id).first()
        nt.assert_is_not_none(institution_storage)
        nt.assert_equals(institution_storage.name, 'My storage')

        wb_credentials = institution_storage.waterbutler_credentials
        nt.assert_equals(wb_credentials['storage']['host'], 'https://valid.owncloud.net')
        nt.assert_equals(wb_credentials['storage']['username'], 'admin')
        nt.assert_equals(wb_credentials['storage']['password'], '1234')

        wb_settings = institution_storage.waterbutler_settings
        nt.assert_equals(wb_settings['storage']['provider'], 'owncloud')
        nt.assert_equals(wb_settings['storage']['folder'], '/reserved_for_osf/')

class TestNextCloudStorageSaveCredentials(AdminTestCase):
    def setUp(self):
        super(TestNextCloudStorageSaveCredentials, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    @mock.patch('admin.rdm_custom_storage_location.utils.test_owncloud_connection')
    def test_connection_fail(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'NG'}, httplib.BAD_REQUEST

        response = self.view_post({
            'storage_name': 'My storage',
            'nextcloud_host': 'drop database;',
            'nextcloud_username': 'invalid-user',
            'nextcloud_password': 'invalid-password',
            'nextcloud_folder': 'Hello World',
            'provider_short_name': 'nextcloud',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('NG', response.content)
        nt.assert_false(Region.objects.filter(_id=self.institution._id).exists())

    @mock.patch('admin.rdm_custom_storage_location.utils.test_owncloud_connection')
    def test_success(self, mock_testconnection):
        mock_testconnection.return_value = {'message': 'Nice'}, httplib.OK

        response = self.view_post({
            'storage_name': 'My storage',
            'nextcloud_host': 'valid.nextcloud.net',
            'nextcloud_username': 'admin',
            'nextcloud_password': '1234',
            'nextcloud_folder': 'reserved_for_osf',
            'provider_short_name': 'nextcloud',
        })

        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('Saved credentials successfully!!', response.content)

        institution_storage = Region.objects.filter(_id=self.institution._id).first()
        nt.assert_is_not_none(institution_storage)
        nt.assert_equals(institution_storage.name, 'My storage')

        wb_credentials = institution_storage.waterbutler_credentials
        nt.assert_equals(wb_credentials['storage']['host'], 'https://valid.nextcloud.net')
        nt.assert_equals(wb_credentials['storage']['username'], 'admin')
        nt.assert_equals(wb_credentials['storage']['password'], '1234')

        wb_settings = institution_storage.waterbutler_settings
        nt.assert_equals(wb_settings['storage']['provider'], 'nextcloud')
        nt.assert_equals(wb_settings['storage']['folder'], '/reserved_for_osf/')

class TestGoogleDriveStorageSaveCredentials(AdminTestCase):
    def setUp(self):
        super(TestGoogleDriveStorageSaveCredentials, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()
        self.seed_data = {
            'provider_name': 'googledrive',
            'oauth_key': 'pzN7NJr1EDzXDHsoZRqJT6jHVkt7ryhQbOzQjiduLmPw8CHs8lzrUBrBiztMQvxK5KLplhpKuGxeP91W',
            'oauth_secret': 'qgKnksgBkx76yCl9CqtTP4DOzPYiHLN9LSHFoVsgLgCc6ZqXngWMww5ydxrqY6OzyjUAcP5wL8c58D1Z',
            'expires_at': timezone.now(),
            'refresh_token': 'e97DkIMV6B0j6NjD1CYIiAm4',
            'date_last_refreshed': timezone.now(),
            'display_name': 'google drive display name is here',
            'profile_url': 'example.com',
            '_id': self.institution._id,
            'provider_id': '88080800880',
        }

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    def view_post_cancel(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.remove_auth_data_temporary(request)

    def test_cancel(self):
        response = self.view_post_cancel({
            'provider_short_name': 'googledrive',
        })
        nt.assert_equals(response.status_code, httplib.OK)

    def test_provider_missing(self):
        response = self.view_post({
            'no_pro': 'googledrive',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_storage_name_missing(self):
        response = self.view_post({
            'provider_short_name': 'googledrive',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Storage name is missing.', response.content)

    def test_googledrive_folder_missing(self):
        response = self.view_post({
            'provider_short_name': 'googledrive',
            'storage_name': 'storage_name',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Folder ID is missing.', response.content)

    def test_success(self):
        ExternalAccountTemporary.objects.create(
            provider=self.seed_data['provider_name'],
            provider_name=self.seed_data['provider_name'],
            oauth_key=self.seed_data['oauth_key'],
            oauth_secret=self.seed_data['oauth_secret'],
            expires_at=self.seed_data['expires_at'],
            refresh_token=self.seed_data['refresh_token'],
            date_last_refreshed=self.seed_data['date_last_refreshed'],
            display_name=self.seed_data['display_name'],
            profile_url=self.seed_data['profile_url'],
            _id=self.seed_data['_id'],
            provider_id=self.seed_data['provider_id'],
        )
        response = self.view_post({
            'provider_short_name': 'googledrive',
            'storage_name': 'storage_name',
            'googledrive_folder': 'root',
        })
        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('OAuth was set successfully', response.content)

        external_account = ExternalAccount.objects.get(
            provider=self.seed_data['provider_name'], provider_id=self.seed_data['provider_id'])
        nt.assert_equals(external_account.oauth_key, self.seed_data['oauth_key'])
        nt.assert_equals(external_account.oauth_secret, self.seed_data['oauth_secret'])

        nt.assert_false(ExternalAccountTemporary.objects.filter(_id=self.institution._id))

        institution_storage = Region.objects.filter(_id=self.institution._id).first()
        nt.assert_is_not_none(institution_storage)
        nt.assert_equals(institution_storage.name, 'storage_name')

        wb_credentials = institution_storage.waterbutler_credentials
        nt.assert_equals(wb_credentials['storage']['token'], self.seed_data['oauth_key'])

        wb_settings = institution_storage.waterbutler_settings
        nt.assert_equals(wb_settings['storage']['folder']['id'], 'root')


class TestBoxSaveCredentials(AdminTestCase):
    def setUp(self):
        super(TestBoxSaveCredentials, self).setUp()
        self.institution = InstitutionFactory()
        self.user = AuthUserFactory()
        self.user.affiliated_institutions.add(self.institution)
        self.user.is_staff = True
        self.user.save()
        self.seed_data = {
            'provider_name': 'box',
            'oauth_key': 'pzN7NJr1EDzXDHsoZRqJT6jHVkt7ryhQbOzQjiduLmPw8CHs8lzrUBrBiztMQvxK5KLplhpKuGxeP91W',
            'oauth_secret': 'qgKnksgBkx76yCl9CqtTP4DOzPYiHLN9LSHFoVsgLgCc6ZqXngWMww5ydxrqY6OzyjUAcP5wL8c58D1Z',
            'expires_at': timezone.now(),
            'refresh_token': 'e97DkIMV6B0j6NjD1CYIiAm4',
            'date_last_refreshed': timezone.now(),
            'display_name': 'box display name is here',
            'profile_url': 'example.com',
            '_id': self.institution._id,
            'provider_id': '88080800880',
        }

    def view_post(self, params):
        request = RequestFactory().post(
            'fake_path',
            json.dumps(params),
            content_type='application/json'
        )
        request.is_ajax()
        request.user = self.user
        return views.save_credentials(request)

    def test_provider_missing(self):
        response = self.view_post({
            'no_pro': 'box',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Provider is missing.', response.content)

    def test_storage_name_missing(self):
        response = self.view_post({
            'provider_short_name': 'box',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Storage name is missing.', response.content)

    def test_googledrive_folder_missing(self):
        response = self.view_post({
            'provider_short_name': 'box',
            'storage_name': 'storage_name',
        })

        nt.assert_equals(response.status_code, httplib.BAD_REQUEST)
        nt.assert_in('Folder is missing.', response.content)

    def test_success(self):
        ExternalAccountTemporary.objects.create(
            provider=self.seed_data['provider_name'],
            provider_name=self.seed_data['provider_name'],
            oauth_key=self.seed_data['oauth_key'],
            oauth_secret=self.seed_data['oauth_secret'],
            expires_at=self.seed_data['expires_at'],
            refresh_token=self.seed_data['refresh_token'],
            date_last_refreshed=self.seed_data['date_last_refreshed'],
            display_name=self.seed_data['display_name'],
            profile_url=self.seed_data['profile_url'],
            _id=self.seed_data['_id'],
            provider_id=self.seed_data['provider_id'],
        )
        response = self.view_post({
            'provider_short_name': 'box',
            'storage_name': 'storage_name',
            'box_folder': '0',
        })
        nt.assert_equals(response.status_code, httplib.OK)
        nt.assert_in('OAuth was set successfully', response.content)

        external_account = ExternalAccount.objects.get(
            provider=self.seed_data['provider_name'], provider_id=self.seed_data['provider_id'])
        nt.assert_equals(external_account.oauth_key, self.seed_data['oauth_key'])
        nt.assert_equals(external_account.oauth_secret, self.seed_data['oauth_secret'])

        nt.assert_false(ExternalAccountTemporary.objects.filter(_id=self.institution._id))

        institution_storage = Region.objects.filter(_id=self.institution._id).first()
        nt.assert_is_not_none(institution_storage)
        nt.assert_equals(institution_storage.name, 'storage_name')

        wb_credentials = institution_storage.waterbutler_credentials
        nt.assert_equals(wb_credentials['storage']['token'], self.seed_data['oauth_key'])

        wb_settings = institution_storage.waterbutler_settings
        nt.assert_equals(wb_settings['storage']['folder'], '0')