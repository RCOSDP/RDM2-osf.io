# -*- coding: utf-8 -*-
from nose.tools import *  # PEP8 asserts

import framework
from framework.auth import Auth
from webtest.app import AppError
from tests.base import OsfTestCase
from tests.factories import (
    UserFactory, NodeFactory, PointerFactory, ProjectFactory, ApiKeyFactory,
    AuthUserFactory, NodeWikiFactory,
)

from website.addons.wiki.views import get_wiki_url, serialize_wiki_toc


class TestWikiViews(OsfTestCase):

    def setUp(self):
        super(TestWikiViews, self).setUp()
        self.project = ProjectFactory(is_public=True)

    def test_get_wiki_url_for_project(self):
        node = ProjectFactory()
        expected = framework.url_for(
            'OsfWebRenderer__project_wiki_page',
            pid=node._primary_key,
            wid='home'
        )
        assert_equal(get_wiki_url(node), expected)

    def test_wiki_url_get_returns_200(self):
        url = get_wiki_url(self.project)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

    def test_wiki_url_for_pointer_returns_200(self):
        pointer = PointerFactory(node=self.project)
        url = get_wiki_url(pointer)
        res = self.app.get(url)
        assert_equal(res.status_code, 200)

    def test_wiki_content_returns_200(self):
        node = ProjectFactory()
        url = node.api_url_for('wiki_page_content', wid='somerandomid')
        res = self.app.get(url).follow()
        assert_equal(res.status_code, 200)

    def test_wiki_url_for_component_returns_200(self):
        component = NodeFactory(project=self.project)
        url = get_wiki_url(component)
        res = self.app.get(url).follow()
        assert_equal(res.status_code, 200)

    def test_serialize_wiki_toc(self):
        project = ProjectFactory()
        auth = Auth(project.creator)
        has_wiki = NodeFactory(project=project, creator=project.creator)
        no_wiki = NodeFactory(project=project, creator=project.creator)
        project.save()

        serialized = serialize_wiki_toc(project, auth=auth)
        assert_equal(len(serialized), 2)
        no_wiki.delete_addon('wiki', auth=auth)
        serialized = serialize_wiki_toc(project, auth=auth)
        assert_equal(len(serialized), 1)

    def test_get_wiki_url_pointer_component(self):
        """Regression test for issue
        https://github.com/CenterForOpenScience/osf/issues/363

        """
        user = UserFactory()
        pointed_node = NodeFactory(creator=user)
        project = ProjectFactory(creator=user)
        auth = Auth(user=user)
        project.add_pointer(pointed_node, auth=auth, save=True)

        serialize_wiki_toc(project, auth)


class TestWikiRename(OsfTestCase):

    def setUp(self):

        super(TestWikiRename, self).setUp()

        self.project = ProjectFactory(is_public=True)
        api_key = ApiKeyFactory()
        self.project.creator.api_keys.append(api_key)
        self.project.creator.save()
        self.consolidate_auth = Auth(user=self.project.creator, api_key=api_key)
        self.auth = ('test', api_key._primary_key)
        self.project.update_node_wiki('home', 'Hello world', self.consolidate_auth)
        self.wiki = self.project.get_wiki_page('home')
        self.url = self.project.api_url_for(
            'project_wiki_rename',
            wid=self.wiki._id,
        )

    def test_rename_wiki_page_valid(self):
        new_name = 'away'
        self.app.put_json(
            self.url,
            {'value': new_name, 'pk': self.wiki._id},
            auth=self.auth,
        )
        self.project.reload()

        old_wiki = self.project.get_wiki_page('home')
        assert_false(old_wiki)

        new_wiki = self.project.get_wiki_page(new_name)
        assert_true(new_wiki)
        assert_equal(new_wiki._id, self.wiki._id)
        assert_equal(new_wiki.content, self.wiki.content)
        assert_equal(new_wiki.version, self.wiki.version)

    def test_rename_wiki_page_invalid(self):
        new_name = '<html>hello</html>'

        with assert_raises(AppError) as cm:
            self.app.put_json(self.url, {'value': new_name, 'pk': self.wiki._id}, auth=self.auth)

            e = cm.exception
            assert_equal(e, 422)

    def test_rename_wiki_page_duplicate(self):
        self.project.update_node_wiki('away', 'Hello world', self.consolidate_auth)
        new_name = 'away'

        with assert_raises(AppError) as cm:
            self.app.put_json(
                self.url,
                {'value': new_name, 'pk': self.wiki._id},
                auth=self.auth,
            )

            e = cm.exception
            assert_equal(e, 409)


class TestWikiLinks(OsfTestCase):

    def test_links(self):
        user = AuthUserFactory()
        project = ProjectFactory(creator=user)
        wiki = NodeWikiFactory(
            content='[[wiki2]]',
            user=user,
            node=project,
        )
        assert_in(
            project.web_url_for('project_wiki_page', wid='wiki2'),
            wiki.html(project),
        )

