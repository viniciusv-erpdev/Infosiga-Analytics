from io import BytesIO
from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from analytics.services.file_loader import build_preview_data, process_upload
from analytics.services.preprocessing.address_cluster import cluster_addresses
from analytics.services.preprocessing.address_dictionary import build_address_dictionary
from analytics.services.preprocessing.address_matcher import regularize_addresses
from analytics.services.preprocessing.address_semantic_cleaner import clean_semantic_address
from analytics.services.preprocessing.apply_manual_corrections import apply_manual_corrections
from analytics.services.preprocessing.pipeline import run_preprocessing


class AuthFlowTests(TestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_user_can_register_and_login(self):
        response = self.client.post(
            reverse("register"),
            {"username": "novo_usuario", "password1": "SenhaForte123", "password2": "SenhaForte123"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        user = get_user_model().objects.get(username="novo_usuario")
        self.assertTrue(user.check_password("SenhaForte123"))
        self.assertNotEqual(user.password, "SenhaForte123")

        login_response = self.client.post(
            reverse("login"),
            {"username": "novo_usuario", "password": "SenhaForte123"},
            follow=True,
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.wsgi_request.user.is_authenticated)

    def test_duplicate_username_is_rejected(self):
        get_user_model().objects.create_user(username="duplicado", password="SenhaForte123")

        response = self.client.post(
            reverse("register"),
            {"username": "duplicado", "password1": "SenhaForte123", "password2": "SenhaForte123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este nome de usuário já existe")

    def test_bad_password_is_rejected(self):
        get_user_model().objects.create_user(username="senha_errada", password="SenhaForte123")

        response = self.client.post(
            reverse("login"),
            {"username": "senha_errada", "password": "errada"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Por favor, entre com um usuário e senha corretos")

    def test_logout_clears_session(self):
        user = get_user_model().objects.create_user(username="logout_user", password="SenhaForte123")
        self.client.force_login(user)

        response = self.client.get(reverse("logout"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class ProcessUploadTests(SimpleTestCase):
    def _build_request(self):
        file_data = BytesIO(b"tipo_registro;municipio;tipo_via;logradouro\nSINISTRO FATAL;RIBEIRAO PRETO;VIAS URBANAS;Av. Independencia\n")
        uploaded_file = SimpleUploadedFile("sample.csv", file_data.getvalue(), content_type="text/csv")

        request = RequestFactory().post(
            "/upload/",
            data={
                "tipo_via": "urbana",
                "tipo_sinistro": "fatal",
                "arquivo": uploaded_file,
            },
            format="multipart",
        )
        request.session = SessionStore()
        setattr(request, "_messages", FallbackStorage(request))
        return request

    @patch("analytics.services.file_loader.load_dataframe")
    def test_process_upload_loads_dataframe_once_and_builds_preview(self, mock_load_dataframe):
        dataframe = pd.DataFrame(
            {
                "tipo_registro": ["SINISTRO FATAL", "SINISTRO FATAL"],
                "municipio": ["RIBEIRAO PRETO", "RIBEIRAO PRETO"],
                "tipo_via": ["VIAS URBANAS", "VIAS URBANAS"],
                "logradouro": ["Av. Independencia", "Rua Teste"],
            }
        )
        mock_load_dataframe.return_value = dataframe

        request = self._build_request()
        form, response = process_upload(request)

        self.assertTrue(form.is_valid())
        self.assertEqual(mock_load_dataframe.call_count, 1)
        self.assertEqual(request.session["preview_data"]["columns"], ["logradouro", "logradouro_normalizado"])
        self.assertEqual(request.session["preview_data"]["rows"][0][0], "Av. Independencia")
        self.assertEqual(response.status_code, 302)

    def test_cluster_addresses_groups_similar_addresses(self):
        clusters = cluster_addresses(["avenida independencia", "av independencia", "rua teste", "avenida independencia"])

        self.assertIn("avenida independencia", clusters)
        self.assertEqual(clusters["avenida independencia"]["frequencia"], 3)
        self.assertIn("av independencia", clusters["avenida independencia"]["membros"])

    def test_build_address_dictionary_maps_variations_to_canonical(self):
        clusters = cluster_addresses(["avenida independencia", "av independencia"])
        dictionary = build_address_dictionary(clusters)

        self.assertEqual(dictionary["av independencia"], "avenida independencia")
        self.assertEqual(dictionary["avenida independencia"], "avenida independencia")

    def test_regularize_addresses_adds_suggested_columns(self):
        dataframe = pd.DataFrame(
            {
                "logradouro_normalizado": ["avenida independencia", "av independencia", "rua teste"],
            }
        )

        regularized = regularize_addresses(dataframe)

        self.assertIn("logradouro_sugerido", regularized.columns)
        self.assertIn("logradouro_canonico", regularized.columns)
        self.assertIn("similaridade", regularized.columns)
        self.assertIn("frequencia_grupo", regularized.columns)
        self.assertEqual(regularized.loc[0, "logradouro_sugerido"], "avenida independencia")
        self.assertEqual(regularized.loc[0, "logradouro_canonico"], "")
        self.assertEqual(regularized.loc[0, "frequencia_grupo"], 1)

    def test_regularize_addresses_preserves_manual_correction_and_suggests_also(self):
        dataframe = pd.DataFrame(
            {
                "logradouro_limpo": ["avenida independencia", "rua teste"],
                "logradouro_canonico": ["Avenida Independencia", ""],
                "correcao_manual_aplicada": [True, False],
            }
        )

        regularized = regularize_addresses(dataframe)

        self.assertEqual(regularized.loc[0, "logradouro_sugerido"], "avenida independencia")
        self.assertEqual(regularized.loc[0, "logradouro_canonico"], "Avenida Independencia")
        self.assertEqual(regularized.loc[0, "confianca_matching"], "MANUAL")
        self.assertEqual(regularized.loc[1, "logradouro_sugerido"], "rua teste")
        self.assertEqual(regularized.loc[1, "logradouro_canonico"], "")

    def test_apply_manual_corrections_sets_canonico_and_flag(self):
        dataframe = pd.DataFrame(
            {
                "logradouro_limpo": ["avenida independencia", "rua teste"],
            }
        )

        with patch("analytics.services.preprocessing.apply_manual_corrections.get_approved_corrections_by_limpos") as mock_get:
            mock_get.return_value = {
                "avenida independencia": type(
                    "Correction",
                    (),
                    {"logradouro_canonico": "Avenida Independencia"},
                )()
            }
            corrected = apply_manual_corrections(dataframe)

        self.assertTrue(corrected.loc[0, "correcao_manual_aplicada"])
        self.assertEqual(corrected.loc[0, "logradouro_canonico"], "Avenida Independencia")
        self.assertFalse(corrected.loc[1, "correcao_manual_aplicada"])
        self.assertEqual(corrected.loc[1, "logradouro_canonico"], "")

    def test_pipeline_preserves_manual_correction_over_suggestion(self):
        dataframe = pd.DataFrame(
            {
                "logradouro": ["AVENIDA PRESIDENTE VARGAS", "RUA TESTE"],
            }
        )

        with patch("analytics.services.preprocessing.apply_manual_corrections.get_approved_corrections_by_limpos") as mock_get:
            mock_get.return_value = {
                "avenida presidente vargas": type(
                    "Correction",
                    (),
                    {"logradouro_canonico": "Avenida Presidente Vargas"},
                )()
            }

            processed = run_preprocessing(dataframe)

        self.assertEqual(processed.loc[0, "logradouro_sugerido"], "avenida presidente vargas")
        self.assertEqual(processed.loc[0, "logradouro_canonico"], "Avenida Presidente Vargas")
        self.assertTrue(processed.loc[0, "correcao_manual_aplicada"])
        self.assertEqual(processed.loc[1, "logradouro_canonico"], "")
        self.assertEqual(processed.loc[1, "logradouro_sugerido"], "rua teste")

    def test_build_preview_data_includes_regularization_columns(self):
        dataframe = pd.DataFrame(
            {
                "logradouro": ["Av. Independencia"],
                "logradouro_normalizado": ["avenida independencia"],
                "logradouro_canonico": ["avenida independencia"],
                "similaridade": [100],
                "frequencia_grupo": [2],
            }
        )

        preview_data = build_preview_data(dataframe)

        self.assertEqual(
            preview_data["regularization_columns"],
            ["logradouro", "logradouro_normalizado", "logradouro_canonico", "similaridade", "frequencia_grupo"],
        )

    def test_clean_semantic_address_removes_known_prefixes(self):
        self.assertEqual(clean_semantic_address("lateral da rodovia anhanguera"), "rodovia anhanguera")
        self.assertEqual(clean_semantic_address("marginal da avenida independencia"), "avenida independencia")
        self.assertEqual(clean_semantic_address("alça de acesso da rodovia anhanguera"), "rodovia anhanguera")
        self.assertEqual(clean_semantic_address("rodovia anhanguera km 10"), "rodovia anhanguera")

    def test_build_preview_data_includes_audit_rows_for_template(self):
        dataframe = pd.DataFrame({"logradouro": ["Av. Independencia", "Rua Teste"]})

        preview_data = build_preview_data(dataframe)

        self.assertEqual(
            preview_data["audit_columns"],
            [
                "Logradouro original",
                "Logradouro normalizado",
                "Logradouro limpo",
                "Logradouro canônico",
                "Similaridade (%)",
                "Frequência do grupo",
            ],
        )
        self.assertEqual(preview_data["audit_rows"][0][0], "Av. Independencia")
        self.assertEqual(preview_data["audit_rows"][0][1], "avenida independencia")
        self.assertEqual(preview_data["audit_rows"][0][2], "avenida independencia")
        self.assertEqual(preview_data["audit_rows"][0][3], "avenida independencia")
        self.assertEqual(preview_data["audit_rows"][0][4], "-")
        self.assertEqual(preview_data["audit_rows"][0][5], 0)
