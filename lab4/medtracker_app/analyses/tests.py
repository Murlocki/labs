from datetime import timedelta
from unittest import mock, skipUnless

from django.contrib.auth.models import User
from django.db import OperationalError, connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from .models import Analysis, AnalysisValue, Unit


# SQLite сравнивает без учёта регистра только латиницу, поэтому проверки
# регистронезависимости для кириллицы выполняются только на PostgreSQL.
postgres_only = skipUnless(connection.vendor == "postgresql", "кириллица без учёта регистра — только PostgreSQL")


def dt_input(value):
    return timezone.localtime(value).strftime("%Y-%m-%dT%H:%M")


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="S3cure-pass-1")
        self.other = User.objects.create_user("bob", password="S3cure-pass-2")
        self.unit = Unit.objects.get(name="ммоль/л")
        self.client.force_login(self.user)

    def make_analysis(self, name="Глюкоза", user=None):
        return Analysis.objects.create(user=user or self.user, name=name, unit=self.unit)


class SeedTests(TestCase):
    def test_units_seeded(self):
        self.assertEqual(Unit.objects.count(), 18)


class AuthTests(TestCase):
    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse("analysis_list"))
        self.assertRedirects(response, "/accounts/login/?next=/analyses/")

    def test_signup_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "newuser", "password1": "Very-strong-9", "password2": "Very-strong-9"},
        )
        self.assertRedirects(response, reverse("analysis_list"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), User.objects.get(username="newuser").pk)

    def test_login_wrong_password(self):
        User.objects.create_user("alice", password="S3cure-pass-1")
        response = self.client.post(reverse("login"), {"username": "alice", "password": "wrong"})
        self.assertContains(response, "Неверный логин или пароль")

    def test_inactive_user_cannot_login(self):
        User.objects.create_user("alice", password="S3cure-pass-1", is_active=False)
        response = self.client.post(reverse("login"), {"username": "alice", "password": "S3cure-pass-1"})
        self.assertContains(response, "Неверный логин или пароль")

    def test_logout(self):
        user = User.objects.create_user("alice", password="S3cure-pass-1")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_admin_forbidden_for_regular_user(self):
        self.client.force_login(User.objects.create_user("alice", password="S3cure-pass-1"))
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])


class AnalysisTests(BaseTestCase):
    def test_list_shows_own_analyses_with_count(self):
        analysis = self.make_analysis()
        AnalysisValue.objects.create(analysis=analysis, value="5.4")
        self.make_analysis("Чужой анализ", user=self.other)
        response = self.client.get(reverse("analysis_list"))
        self.assertContains(response, "Глюкоза")
        self.assertNotContains(response, "Чужой анализ")
        self.assertEqual(response.context["analyses"][0].values_count, 1)

    def test_list_empty_and_search(self):
        response = self.client.get(reverse("analysis_list"))
        self.assertContains(response, "У вас пока нет анализов")
        self.make_analysis()
        self.make_analysis("Гемоглобин")
        response = self.client.get(reverse("analysis_list"), {"q": "Глюк"})
        self.assertContains(response, "Глюкоза")
        self.assertNotContains(response, "Гемоглобин")
        response = self.client.get(reverse("analysis_list"), {"q": "xyz"})
        self.assertContains(response, "Ничего не найдено")

    def test_create(self):
        response = self.client.post(
            reverse("analysis_create"), {"name": "  Глюкоза  ", "unit": self.unit.pk, "description": "норма 3.9–5.5"}
        )
        analysis = Analysis.objects.get()
        self.assertEqual(analysis.name, "Глюкоза")
        self.assertEqual(analysis.user, self.user)
        self.assertRedirects(response, reverse("analysis_detail", args=[analysis.pk]))

    def test_create_duplicate(self):
        self.make_analysis()
        response = self.client.post(reverse("analysis_create"), {"name": "Глюкоза"})
        self.assertContains(response, "Анализ с таким названием уже существует")
        self.assertEqual(Analysis.objects.count(), 1)

    @postgres_only
    def test_create_duplicate_case_insensitive(self):
        self.make_analysis()
        response = self.client.post(reverse("analysis_create"), {"name": "глюкоза"})
        self.assertContains(response, "Анализ с таким названием уже существует")
        self.assertEqual(Analysis.objects.count(), 1)

    @postgres_only
    def test_search_case_insensitive(self):
        self.make_analysis()
        response = self.client.get(reverse("analysis_list"), {"q": "глюк"})
        self.assertContains(response, "Глюкоза")

    def test_same_name_allowed_for_other_user(self):
        self.make_analysis(user=self.other)
        self.client.post(reverse("analysis_create"), {"name": "Глюкоза"})
        self.assertEqual(Analysis.objects.filter(user=self.user).count(), 1)

    def test_update_keeps_own_name(self):
        analysis = self.make_analysis()
        response = self.client.post(reverse("analysis_update", args=[analysis.pk]), {"name": "Глюкоза", "unit": ""})
        self.assertRedirects(response, reverse("analysis_detail", args=[analysis.pk]))
        analysis.refresh_from_db()
        self.assertIsNone(analysis.unit)

    def test_delete_cascades_values(self):
        analysis = self.make_analysis()
        AnalysisValue.objects.create(analysis=analysis, value="5.4")
        response = self.client.get(reverse("analysis_delete", args=[analysis.pk]))
        self.assertContains(response, "(1 шт.)")
        response = self.client.post(reverse("analysis_delete", args=[analysis.pk]))
        self.assertRedirects(response, reverse("analysis_list"))
        self.assertFalse(Analysis.objects.exists())
        self.assertFalse(AnalysisValue.objects.exists())

    def test_foreign_analysis_404(self):
        foreign = self.make_analysis(user=self.other)
        for name in ("analysis_detail", "analysis_update", "analysis_delete", "analysis_value_create"):
            response = self.client.get(reverse(name, args=[foreign.pk]))
            self.assertEqual(response.status_code, 404, name)
        self.client.post(reverse("analysis_delete", args=[foreign.pk]))
        self.assertTrue(Analysis.objects.filter(pk=foreign.pk).exists())


class ValueTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.analysis = self.make_analysis()

    def test_create_from_analysis_page(self):
        response = self.client.get(reverse("analysis_value_create", args=[self.analysis.pk]))
        self.assertEqual(response.context["form"].initial["analysis"], self.analysis)
        when = timezone.now() - timedelta(hours=1)
        response = self.client.post(
            reverse("analysis_value_create", args=[self.analysis.pk]),
            {"analysis": self.analysis.pk, "value": "120/80", "measured_at": dt_input(when), "note": "натощак"},
        )
        self.assertRedirects(response, reverse("analysis_detail", args=[self.analysis.pk]))
        self.assertEqual(self.analysis.entries.get().value, "120/80")

    def test_values_sorted_newest_first(self):
        now = timezone.now()
        AnalysisValue.objects.create(analysis=self.analysis, value="old", measured_at=now - timedelta(days=5))
        AnalysisValue.objects.create(analysis=self.analysis, value="new", measured_at=now - timedelta(days=1))
        response = self.client.get(reverse("analysis_detail", args=[self.analysis.pk]))
        self.assertEqual([e.value for e in response.context["entries"]], ["new", "old"])

    def test_future_date_rejected(self):
        response = self.client.post(
            reverse("value_create"),
            {"analysis": self.analysis.pk, "value": "5.4", "measured_at": dt_input(timezone.now() + timedelta(days=1))},
        )
        self.assertContains(response, "Дата сдачи не может быть в будущем")
        self.assertFalse(AnalysisValue.objects.exists())

    def test_cannot_attach_value_to_foreign_analysis(self):
        foreign = self.make_analysis(user=self.other)
        response = self.client.post(
            reverse("value_create"),
            {"analysis": foreign.pk, "value": "5.4", "measured_at": dt_input(timezone.now())},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AnalysisValue.objects.exists())

    def test_update_and_delete(self):
        entry = AnalysisValue.objects.create(analysis=self.analysis, value="5.4")
        response = self.client.post(
            reverse("value_update", args=[entry.pk]),
            {"analysis": self.analysis.pk, "value": "5.9", "measured_at": dt_input(entry.measured_at), "note": ""},
        )
        self.assertRedirects(response, reverse("analysis_detail", args=[self.analysis.pk]))
        entry.refresh_from_db()
        self.assertEqual(entry.value, "5.9")
        response = self.client.post(reverse("value_delete", args=[entry.pk]))
        self.assertRedirects(response, reverse("analysis_detail", args=[self.analysis.pk]))
        self.assertFalse(AnalysisValue.objects.exists())

    def test_foreign_value_404(self):
        foreign = AnalysisValue.objects.create(analysis=self.make_analysis(user=self.other), value="1")
        for name in ("value_update", "value_delete"):
            self.assertEqual(self.client.get(reverse(name, args=[foreign.pk])).status_code, 404, name)


class PaginationTests(BaseTestCase):
    def test_values_paginated_by_50(self):
        analysis = self.make_analysis()
        now = timezone.now()
        AnalysisValue.objects.bulk_create(
            AnalysisValue(analysis=analysis, value=str(i), measured_at=now - timedelta(minutes=i)) for i in range(120)
        )
        url = reverse("analysis_detail", args=[analysis.pk])
        response = self.client.get(url)
        self.assertEqual(len(response.context["entries"]), 50)
        self.assertEqual(response.context["entries"][0].value, "0")
        self.assertContains(response, "Страница 1 из 3")
        response = self.client.get(url, {"page": 3})
        self.assertEqual([e.value for e in response.context["entries"]][-1], "119")
        self.assertEqual(len(response.context["entries"]), 20)

    def test_detail_query_count(self):
        analysis = self.make_analysis()
        AnalysisValue.objects.create(analysis=analysis, value="1")
        url = reverse("analysis_detail", args=[analysis.pk])
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(url)
        domain = [q for q in ctx.captured_queries if "analyses_" in q["sql"]]
        self.assertLessEqual(len(domain), 3)  # анализ, количество значений, страница значений

    def test_list_single_query(self):
        self.make_analysis()
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse("analysis_list"))
        self.assertEqual(len([q for q in ctx.captured_queries if "analyses_" in q["sql"]]), 1)


class DatabaseUnavailableTests(BaseTestCase):
    def test_db_error_shows_friendly_page(self):
        with (
            mock.patch("analyses.views.AnalysisListView.get_queryset", side_effect=OperationalError("no connection")),
            self.assertLogs("analyses.middleware", level="ERROR"),
        ):
            response = self.client.get(reverse("analysis_list"))
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Сервер базы данных недоступен", status_code=503)


class DeleteTextTests(BaseTestCase):
    def test_value_delete_confirmation_text(self):
        entry = AnalysisValue.objects.create(
            analysis=self.make_analysis(), value="5.4", measured_at=timezone.make_aware(timezone.datetime(2026, 9, 27, 10, 30))
        )
        response = self.client.get(reverse("value_delete", args=[entry.pk]))
        self.assertContains(response, "Удалить значение 5.4 ммоль/л от 27.09.2026 10:30?")


class ErrorPagesTests(TestCase):
    def test_404_page_in_russian(self):
        response = self.client.get("/nonexistent/", HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertContains(response, "Страница не найдена", status_code=404)

    def test_csrf_failure_page_in_russian(self):
        client = self.client_class(enforce_csrf_checks=True)
        response = client.post(reverse("login"), {"username": "a", "password": "b"})
        self.assertContains(response, "Форма устарела", status_code=403)

    def test_logout_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

    def test_interface_language_does_not_depend_on_browser(self):
        response = self.client.get(reverse("login"), HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertContains(response, "Имя пользователя")
