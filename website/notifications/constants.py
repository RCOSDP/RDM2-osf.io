from django.utils.translation import ugettext_lazy as _

NODE_SUBSCRIPTIONS_AVAILABLE = {
    'comments': unicode(_('Comments added')),
    'file_updated': unicode(_('Files updated'))
}

# Note: if the subscription starts with 'global_', it will be treated like a default
# subscription. If no notification type has been assigned, the user subscription
# will default to 'email_transactional'.
USER_SUBSCRIPTIONS_AVAILABLE = {
    'global_comment_replies': unicode(_('Replies to your comments')),
    'global_comments': unicode(_('Comments added')),
    'global_file_updated': unicode(_('Files updated')),
    'global_mentions': unicode(_('Mentions added')),
    'global_reviews': unicode(_('Preprint submissions updated'))
}

PROVIDER_SUBSCRIPTIONS_AVAILABLE = {
    'new_pending_submissions': 'New preprint submissions for moderators to review.'
}

# Note: the python value None mean inherit from parent
NOTIFICATION_TYPES = {
    'email_transactional': 'Email when a change occurs',
    'email_digest': 'Daily email digest of all changes to this project',
    'none': 'None'
}

# Formatted file provider names for notification emails
PROVIDERS = {
    'osfstorage': 'NII Storage',
    'box': 'Box',
    'dataverse': 'Dataverse',
    'dropbox': 'Dropbox',
    'figshare': 'figshare',
    'github': 'GitHub',
    'gitlab': 'GitLab',
    'bitbucket': 'Bitbucket',
    'googledrive': 'Google Drive',
    'owncloud': 'ownCloud',
    'onedrive': 'Microsoft OneDrive',
    's3': 'Amazon S3',
    'swift': 'OpenStack Swift',
    'azureblobstorage': 'Azure Blob Storage',
    'weko': 'WEKO'
}
# install-addons.py
PROVIDERS['s3compat'] = 'S3 Compatible Storage'
PROVIDERS['nextcloud'] = 'Nextcloud'
