from django.conf.urls import patterns, include, url
from survey import views

urlpatterns = patterns('',
    url(r'^section_a/(?P<category_id>[\d]+)/view/(?P<survey_id>[\d]+)$', views.SectionA.as_view(), name='view'),
    url(r'^section_a/(?P<category_id>[\d]+)/edit$', views.SectionAEdit.as_view(), name='edit'),
)
