# -*- coding: utf-8 -*-

import httplib
from django.http import JsonResponse
import os
from website import settings as osf_settings
from addons.s3 import utils as s3_utils

providers = None
enabled_providers_list = [
    's3', 'box', 'googledrive', 'osfstorage',
    'nextcloud', 'swift', 'owncloud', 's3compat'
]

def get_providers():
    provider_list = []
    for provider in osf_settings.ADDONS_AVAILABLE:
        if 'storage' in provider.categories and provider.short_name in enabled_providers_list:
            provider.icon_url_admin = \
                '/custom_storage_location/icon/{}/comicon.png'.format(provider.short_name)
            provider.modal_path = get_modal_path(provider.short_name)
            provider_list.append(provider)
    provider_list.sort(key=lambda x: x.full_name.lower())
    return provider_list

def get_addon_by_name(addon_short_name):
    """get Addon object from Short Name."""
    for addon in osf_settings.ADDONS_AVAILABLE:
        if addon.short_name == addon_short_name:
            return addon
    return None

def get_modal_path(short_name):
    base_path = os.path.join('rdm_custom_storage_location', 'providers')
    return os.path.join(base_path, '{}_modal.html'.format(short_name))

def test_s3_connection(access_key, secret_key):
    """Verifies new external account credentials and adds to user's list"""
    if not (access_key and secret_key):
        return JsonResponse({
            'message': 'All the fields above are required.'
        }, httplib.BAD_REQUEST)
    user_info = s3_utils.get_user_info(access_key, secret_key)
    if not user_info:
        return JsonResponse({
            'message': ('Unable to access account.\n'
                'Check to make sure that the above credentials are valid,'
                'and that they have permission to list buckets.')
        }, status=httplib.BAD_REQUEST)

    if not s3_utils.can_list(access_key, secret_key):
        return JsonResponse({
            'message': ('Unable to list buckets.\n'
                'Listing buckets is required permission that can be changed via IAM')
        }, status=httplib.BAD_REQUEST)
    return JsonResponse({
        'message': ('credentials are valid'),
        'jdata': vars(user_info)
    }, status=httplib.OK)
