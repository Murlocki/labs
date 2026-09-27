from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="analysis_list"), name="home"),
    # учётные записи
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(authentication_form=LoginForm, redirect_authenticated_user=True),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),
    # анализы
    path("analyses/", views.AnalysisListView.as_view(), name="analysis_list"),
    path("analyses/add/", views.AnalysisCreateView.as_view(), name="analysis_create"),
    path("analyses/<int:pk>/", views.AnalysisDetailView.as_view(), name="analysis_detail"),
    path("analyses/<int:pk>/edit/", views.AnalysisUpdateView.as_view(), name="analysis_update"),
    path("analyses/<int:pk>/delete/", views.AnalysisDeleteView.as_view(), name="analysis_delete"),
    # значения анализов
    path("values/add/", views.ValueCreateView.as_view(), name="value_create"),
    path("analyses/<int:analysis_pk>/values/add/", views.ValueCreateView.as_view(), name="analysis_value_create"),
    path("values/<int:pk>/edit/", views.ValueUpdateView.as_view(), name="value_update"),
    path("values/<int:pk>/delete/", views.ValueDeleteView.as_view(), name="value_delete"),
]
