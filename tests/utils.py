import mock
import contextlib
import functools
from nose import SkipTest

from framework.auth import Auth

from website.archiver import listeners as archiver_listeners
from website.archiver import ARCHIVER_SUCCESS

def requires_module(module):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                __import__(module)
            except ImportError:
                raise SkipTest()
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@contextlib.contextmanager
def mock_archive(project, schema=None, auth=None, template=None, data=None, parent=None,
                 autocomplete=True, autoapprove=False):
    """ A context manager for registrations. When you want to call Node#register_node in
    a test but do not want to deal with any of this side effects of archiver, this
    helper allows for creating a registration in a safe fashion.

    :param bool autocomplete: automatically finish archival?
    :param bool autoapprove: automatically approve registration approval?

    Example use:

    project = ProjectFactory()
    with mock_archive(project) as registration:
        assert_true(registration.is_registration)
        assert_true(registration.archiving)
        assert_true(registration.is_pending_registration)

    with mock_archive(project, autocomplete=True) as registration:
        assert_true(registration.is_registration)
        assert_false(registration.archiving)
        assert_true(registration.is_pending_registration)

    with mock_archive(project, autocomplete=True, autoapprove=True) as registration:
        assert_true(registration.is_registration)
        assert_false(registration.archiving)
        assert_false(registration.is_pending_registration)
    """
    schema = schema or None
    auth = auth or Auth(project.creator)
    template = template or ''
    data = data or ''

    with mock.patch('framework.tasks.handlers.enqueue_task'):
        registration = project.register_node(schema, auth, template, data, parent)
    registration.root.require_approval(project.creator)
    if autocomplete:
        root_job = registration.root.archive_job
        root_job.status = ARCHIVER_SUCCESS
        root_job.sent = False
        root_job.done = True
        root_job.save()
        sanction = registration.root.sanction
        with contextlib.nested(
            mock.patch.object(root_job, 'archive_tree_finished', mock.Mock(return_value=True)),
            mock.patch.object(sanction, 'ask')
        ):
            archiver_listeners.archive_callback(registration)
    if autoapprove:
        sanction = registration.root.sanction
        sanction._on_complete(project.creator)
    yield registration
