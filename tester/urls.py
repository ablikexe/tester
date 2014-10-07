from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
) + patterns('tester.views',
    url(r'^login', 'login'),
    url(r'^signup', 'signup'),
    url(r'^logout', 'logout'),
    url(r'^add_task', 'add_task'),
    url(r'^settings', 'settings'),
    url(r'^manage_tasks', 'manage_tasks'),
    url(r'^manage_task/(?P<task_id>[0-9]+)$', 'manage_task'),
    url(r'^manage_task/(?P<task_id>[0-9]+)/tests$', 'manage_tests'),
    url(r'^manage_task/(?P<task_id>[0-9]+)/tests/add_zip', 'add_zip'),
    url(r'^manage_task/(?P<task_id>[0-9]+)/tests/add', 'add_test'),
    url(r'^show_solutions', 'show_solutions'),
    url(r'^show_solution/(?P<solution_id>[0-9]+)', 'show_solution'),
    url(r'^show_query', 'show_query'),
    url(r'^manage_task/(?P<task_id>[0-9]+)', 'manage_task'),
    url(r'^remove_task/(?P<task_id>[0-9]+)', 'remove_task'),
    url(r'^task/(?P<clear_name>[a-z0-9\-]+)/published', 'show_published_task_solutions'),
    url(r'^task/(?P<clear_name>[a-z0-9\-]+)/solutions', 'show_task_solutions'),
    url(r'^test/(?P<task_id>[0-9]+)', 'test'),
    url(r'^task/(?P<clear_name>[a-z0-9\-]+)', 'show_task'),
    url(r'^download_test/(?P<test_id>[0-9]+)', 'download_test'),
    url(r'^top', 'top'),
    url(r'^add_comment', 'add_comment'),
    url(r'^remove_comment', 'remove_comment'),
    url(r'^$', 'show_tasks'),
)
