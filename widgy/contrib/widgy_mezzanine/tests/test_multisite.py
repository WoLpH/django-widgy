from six.moves import http_client

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.unittest import skipUnless
from django.contrib.sites.models import Site
from django.conf import settings
from django.conf.urls import url, include
from django.core.urlresolvers import get_resolver

from argonauts.testutils import JsonTestCase

from widgy.contrib.widgy_mezzanine import get_widgypage_model
from widgy.contrib.widgy_mezzanine.site import WidgySiteMultiSite

from .test_core import UserSetup, PageSetup, TestCase

WidgyPage = get_widgypage_model()
widgy_site = WidgySiteMultiSite()

PAGE_BUILDER_INSTALLED = 'widgy.contrib.page_builder' in settings.INSTALLED_APPS

urlpatterns = get_resolver(None).url_patterns
urlpatterns += [url('^widgy_site/', include(widgy_site.urls))]

@skipUnless(PAGE_BUILDER_INSTALLED, 'page builder is not installed')
@override_settings(WIDGY_MEZZANINE_SITE='widgy.contrib.widgy_mezzanine.tests.test_multisite.widgy_site')
class TestMultiSitePermissions(UserSetup, PageSetup, JsonTestCase, TestCase):
    urls = 'widgy.contrib.widgy_mezzanine.tests.test_multisite'

    def setUp(self):
        import pdb; pdb.set_trace()
        from widgy.contrib.page_builder.models import MainContent
        super(TestMultiSitePermissions, self).setUp()
        self.main_site = Site.objects.get(pk=1)
        self.other_site = Site.objects.create(domain='other.example.com', name='Other')

        self.other_page = WidgyPage.objects.create(
            root_node=self.widgy_site.get_version_tracker_model().objects.create(
                working_copy=MainContent.add_root(self.widgy_site).node,
            ),
            title='titleabc',
            slug='slugabc',
            site=self.other_site,
        )

        self.staffuser.sitepermissions.sites.add(self.main_site)

    def test_cant_create_node_on_other_site(self):
        self.client.login(username='staffuser', password='password')

        parent = self.page.root_node.working_copy.to_json(self.widgy_site)
        response = self.client.post(
            self.widgy_site.reverse(self.widgy_site.node_view),
            {
                '__class__': 'page_builder.Button',
                'parent_id': parent['url'],
                'right_id': None,
            },
            HTTP_HOST=self.main_site.domain,
        )

        self.assertEqual(response.status_code, http_client.CREATED)

        parent = self.other_page.root_node.working_copy.to_json(self.widgy_site)
        response = self.client.post(
            self.widgy_site.reverse(self.widgy_site.node_view),
            {
                '__class__': 'page_builder.Button',
                'parent_id': parent['url'],
                'right_id': None
            },
            HTTP_HOST=self.other_site.domain,
        )

        self.assertEqual(response.status_code, http_client.FORBIDDEN)

    def test_cant_move_around_node_on_other_site(self):
        from widgy.contrib.page_builder.models import Button
        self.client.login(username='staffuser', password='password')

        button = self.page.root_node.working_copy.content.add_child(
            self.widgy_site, Button, text='buttontext')
        sibling = button.add_sibling(self.widgy_site, Button, text='otherbutton')

        parent = self.page.root_node.working_copy.content
        response = self.client.put(
            button.node.get_api_url(self.widgy_site),
            {
                '__class__': 'page_builder.Button',
                'url': sibling.node.get_api_url(self.widgy_site),
                'parent_id': parent.node.get_api_url(self.widgy_site),
                'right_id': button.node.get_api_url(self.widgy_site),
            },
            HTTP_HOST=self.main_site.domain,
        )

        self.assertEqual(response.status_code, http_client.OK)

        button = self.other_page.root_node.working_copy.content.add_child(
            self.widgy_site, Button, text='buttontext')
        sibling = button.add_sibling(self.widgy_site, Button, text='otherbutton')

        parent = self.other_page.root_node.working_copy.content
        response = self.client.put(
            button.node.get_api_url(self.widgy_site),
            {
                '__class__': 'page_builder.Button',
                'url': sibling.node.get_api_url(self.widgy_site),
                'parent_id': parent.node.get_api_url(self.widgy_site),
                'right_id': button.node.get_api_url(self.widgy_site),
            },
            HTTP_HOST=self.other_site.domain,
        )

        self.assertEqual(response.status_code, http_client.FORBIDDEN)

    def test_cant_update_content_on_other_site(self):
        from widgy.contrib.page_builder.models import Button
        self.client.login(username='staffuser', password='password')

        button = self.page.root_node.working_copy.content.add_child(
            self.widgy_site, Button, text='buttontext')

        parent = self.page.root_node.working_copy.content
        response = self.client.put(
            button.get_api_url(self.widgy_site),
            {
                '__class__': 'page_builder.Button',
                'attributes': dict(
                    text='newtext',
                    link='',
                ),
            },
            HTTP_HOST=self.main_site.domain,
        )

        self.assertEqual(response.status_code, http_client.OK)

        button = self.other_page.root_node.working_copy.content.add_child(
            self.widgy_site, Button, text='buttontext')

        parent = self.other_page.root_node.working_copy.content
        response = self.client.put(
            button.get_api_url(self.widgy_site),
            {
                '__class__': 'page_builder.Button',
                'attributes': dict(
                    text='newtext',
                    link='',
                ),
            },
            HTTP_HOST=self.main_site.domain,
        )

        self.assertEqual(response.status_code, http_client.FORBIDDEN)

    def test_cant_delete_content_on_other_site(self):
        from widgy.contrib.page_builder.models import Button
        self.client.login(username='staffuser', password='password')

        button = self.page.root_node.working_copy.content.add_child(
            self.widgy_site, Button, text='buttontext')

        parent = self.page.root_node.working_copy.content
        response = self.client.delete(
            button.node.get_api_url(self.widgy_site),
            HTTP_HOST=self.main_site.domain,
        )

        self.assertEqual(response.status_code, http_client.OK)

        button = self.other_page.root_node.working_copy.content.add_child(
            self.widgy_site, Button, text='buttontext')

        parent = self.other_page.root_node.working_copy.content
        response = self.client.delete(
            button.node.get_api_url(self.widgy_site),
            HTTP_HOST=self.main_site.domain,
        )

        self.assertEqual(response.status_code, http_client.FORBIDDEN)
