from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'tester.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^test/', 'tester.views.test'),
    url(r'^add_task/', 'tester.views.add_task'),
    url(r'^remove_task/(?P<short>[a-zA-Z0-9]+)', 'tester.views.remove_task'),
    url(r'^task/(?P<short>[a-zA-Z0-9]+)', 'tester.views.show_task'),
    url(r'^download_test/(?P<short>[a-zA-Z0-9]+)/(?P<test>[a-zA-Z0-9]+)', 'tester.views.download_test'),
    url(r'', 'tester.views.show_tasks'),
)
