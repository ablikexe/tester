from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login', 'tester.views.login'),
    url(r'^logout', 'tester.views.logout'),
    url(r'^add_task', 'tester.views.add_task'),
    url(r'^manage_tasks', 'tester.views.manage_tasks'),
    url(r'^manage_task/(?P<task_id>[0-9]+)', 'tester.views.manage_task'),
    url(r'^remove_task/(?P<task_id>[0-9]+)', 'tester.views.remove_task'),
    url(r'^task/(?P<clear_name>[a-z0-9\-]+)', 'tester.views.show_task'),
    url(r'^download_test/(?P<test_id>[0-9]+)', 'tester.views.download_test'),
    url(r'^$', 'tester.views.show_tasks'),
)
