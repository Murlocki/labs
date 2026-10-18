from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from .forms import AnalysisForm, AnalysisValueForm, SignUpForm
from .models import Analysis, AnalysisValue


class SignUpView(FormView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("analysis_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("analysis_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Регистрация выполнена.")
        return super().form_valid(form)


# ---------- Анализы ----------


class OwnAnalysisMixin(LoginRequiredMixin):
    """Ограничивает выборку анализами текущего пользователя (чужие → 404)."""

    def get_queryset(self):
        return Analysis.objects.filter(user=self.request.user).select_related("unit")


class AnalysisFormMixin:
    form_class = AnalysisForm
    template_name = "analyses/analysis_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("analysis_detail", args=[self.object.pk])


class AnalysisListView(OwnAnalysisMixin, ListView):
    template_name = "analyses/analysis_list.html"
    context_object_name = "analyses"

    def get_queryset(self):
        qs = super().get_queryset().annotate(values_count=Count("entries")).order_by("name")
        self.query = self.request.GET.get("q", "").strip()
        if self.query:
            qs = qs.filter(name__icontains=self.query)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        return context


class AnalysisDetailView(OwnAnalysisMixin, DetailView):
    template_name = "analyses/analysis_detail.html"
    context_object_name = "analysis"
    values_per_page = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.object.entries.order_by("-measured_at"), self.values_per_page)
        page = paginator.get_page(self.request.GET.get("page"))
        context["page_obj"] = page
        context["entries"] = page.object_list
        return context


class AnalysisCreateView(LoginRequiredMixin, SuccessMessageMixin, AnalysisFormMixin, CreateView):
    success_message = "Анализ добавлен."

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AnalysisUpdateView(OwnAnalysisMixin, SuccessMessageMixin, AnalysisFormMixin, UpdateView):
    success_message = "Анализ изменён."


class AnalysisDeleteView(OwnAnalysisMixin, SuccessMessageMixin, DeleteView):
    template_name = "analyses/analysis_confirm_delete.html"
    context_object_name = "analysis"
    success_url = reverse_lazy("analysis_list")
    success_message = "Анализ удалён."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["values_count"] = self.object.entries.count()
        return context


# ---------- Значения анализов ----------


class OwnValueMixin(LoginRequiredMixin):
    """Ограничивает выборку значениями анализов текущего пользователя (чужие → 404)."""

    def get_queryset(self):
        return AnalysisValue.objects.filter(analysis__user=self.request.user).select_related("analysis__unit")


class ValueFormMixin:
    form_class = AnalysisValueForm
    template_name = "analyses/value_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("analysis_detail", args=[self.object.analysis_id])


class ValueCreateView(LoginRequiredMixin, SuccessMessageMixin, ValueFormMixin, CreateView):
    success_message = "Значение добавлено."

    def dispatch(self, request, *args, **kwargs):
        self.analysis = None
        if request.user.is_authenticated and "analysis_pk" in kwargs:
            self.analysis = get_object_or_404(Analysis, pk=kwargs["analysis_pk"], user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.analysis:
            initial["analysis"] = self.analysis
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analysis"] = self.analysis
        return context


class ValueUpdateView(OwnValueMixin, SuccessMessageMixin, ValueFormMixin, UpdateView):
    success_message = "Значение изменено."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analysis"] = self.object.analysis
        return context


class ValueDeleteView(OwnValueMixin, SuccessMessageMixin, DeleteView):
    template_name = "analyses/value_confirm_delete.html"
    context_object_name = "entry"
    success_message = "Значение удалено."

    def get_success_url(self):
        return reverse("analysis_detail", args=[self.object.analysis_id])
