from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login', 'tester.views.login'),
    url(r'^signup', 'tester.views.signup'),
    url(r'^logout', 'tester.views.logout'),
    url(r'^add_task', 'tester.views.add_task'),
    url(r'^settings', 'tester.views.settings'),
    url(r'^manage_tasks', 'tester.views.manage_tasks'),
    url(r'^manage_task/(?P<task_id>[0-9]+)$', 'tester.views.manage_task'),
    url(r'^manage_task/(?P<task_id>[0-9]+)/tests$', 'tester.views.manage_tests'),
    url(r'^manage_task/(?P<task_id>[0-9]+)/tests/add_zip', 'tester.views.add_zip'),
    url(r'^manage_task/(?P<task_id>[0-9]+)/tests/add', 'tester.views.add_test'),
    url(r'^show_solutions', 'tester.views.show_solutions'),
    url(r'^show_solution/(?P<solution_id>[0-9]+)', 'tester.views.show_solution'),
    url(r'^show_query', 'tester.views.show_query'),
    url(r'^manage_task/(?P<task_id>[0-9]+)', 'tester.views.manage_task'),
    url(r'^remove_task/(?P<task_id>[0-9]+)', 'tester.views.remove_task'),
    url(r'^test/(?P<task_id>[0-9]+)', 'tester.views.test'),
    url(r'^task/(?P<clear_name>[a-z0-9\-]+)', 'tester.views.show_task'),
    url(r'^download_test/(?P<test_id>[0-9]+)', 'tester.views.download_test'),
    url(r'^top', 'tester.views.top'),
    url(r'^$', 'tester.views.show_tasks'),
)
