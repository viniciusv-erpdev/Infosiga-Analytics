from io import BytesIO
from pathlib import Path
import tempfile
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from analytics.models import (
    AddressCorrection,
    CorrectionAudit,
    Dataset,
    DatasetRecordAudit,
)
from analytics.services.dataset_service import DatasetService
from analytics.services.file_loader import (
    build_preview_data,
    load_dataframe,
)
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


class DatasetProcessedFilePersistenceTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.override_media = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.override_media.enable()

        self.user = get_user_model().objects.create_user(
            username="dataset_owner",
            password="SenhaForte123",
        )

    def tearDown(self):
        self.override_media.disable()
        self.media_directory.cleanup()

    def _create_dataset(self, user, filename, value):
        uploaded_file = SimpleUploadedFile(
            filename,
            b"logradouro\nvalor\n",
            content_type="text/csv",
        )
        dataset = DatasetService.create_from_upload(
            usuario=user,
            arquivo=uploaded_file,
            quantidade_registros=1,
        )
        dataframe = pd.DataFrame(
            {
                "logradouro": [value],
                "dataset_value": [value],
            }
        )
        return DatasetService.save_processed_dataframe(dataset, dataframe)

    def test_same_filename_produces_different_parquet_paths(self):
        first = self._create_dataset(self.user, "acidentes.csv", "primeiro")
        second = self._create_dataset(self.user, "acidentes.csv", "segundo")

        self.assertNotEqual(
            first.resultado_processado.name,
            second.resultado_processado.name,
        )
        self.assertIn(f"processed/{first.id}/", first.resultado_processado.name)
        self.assertIn(f"processed/{second.id}/", second.resultado_processado.name)
        self.assertTrue(Path(first.resultado_processado.path).exists())
        self.assertTrue(Path(second.resultado_processado.path).exists())

    def test_same_filename_from_different_users_does_not_collide(self):
        other_user = get_user_model().objects.create_user(
            username="other_dataset_owner",
            password="SenhaForte123",
        )

        first = self._create_dataset(self.user, "acidentes.csv", "primeiro")
        second = self._create_dataset(other_user, "acidentes.csv", "segundo")

        self.assertNotEqual(
            first.resultado_processado.name,
            second.resultado_processado.name,
        )
        self.assertTrue(Path(first.resultado_processado.path).exists())
        self.assertTrue(Path(second.resultado_processado.path).exists())

    def test_delete_only_removes_the_selected_dataset_parquet(self):
        first = self._create_dataset(self.user, "acidentes.csv", "primeiro")
        second = self._create_dataset(self.user, "acidentes.csv", "segundo")
        first_path = Path(first.resultado_processado.path)
        second_path = Path(second.resultado_processado.path)

        DatasetService.delete(first)

        self.assertFalse(first_path.exists())
        self.assertTrue(second_path.exists())

    def test_delete_preserves_legacy_parquet_referenced_by_another_dataset(self):
        first = self._create_dataset(self.user, "acidentes.csv", "primeiro")
        second = self._create_dataset(self.user, "acidentes.csv", "segundo")
        shared_path = Path(first.resultado_processado.path)
        second.resultado_processado.name = first.resultado_processado.name
        second.save(update_fields=["resultado_processado"])

        DatasetService.delete(first)

        self.assertTrue(shared_path.exists())
        second.refresh_from_db()
        self.assertEqual(
            second.resultado_processado.name,
            shared_path.relative_to(self.media_directory.name).as_posix(),
        )

    def test_each_dataset_loads_its_own_processed_content(self):
        first = self._create_dataset(self.user, "acidentes.csv", "primeiro")
        second = self._create_dataset(self.user, "acidentes.csv", "segundo")

        first_loaded = DatasetService.load_processed_dataframe(first)
        second_loaded = DatasetService.load_processed_dataframe(second)

        self.assertEqual(first_loaded.loc[0, "dataset_value"], "primeiro")
        self.assertEqual(second_loaded.loc[0, "dataset_value"], "segundo")

    def test_different_filenames_continue_to_work(self):
        first = self._create_dataset(self.user, "acidentes.csv", "primeiro")
        second = self._create_dataset(self.user, "vitimas.xlsx", "segundo")

        self.assertTrue(first.resultado_processado.name.endswith(
            "acidentes_processado.parquet"
        ))
        self.assertTrue(second.resultado_processado.name.endswith(
            "vitimas_processado.parquet"
        ))
        self.assertEqual(
            DatasetService.load_processed_dataframe(first).loc[0, "dataset_value"],
            "primeiro",
        )
        self.assertEqual(
            DatasetService.load_processed_dataframe(second).loc[0, "dataset_value"],
            "segundo",
        )


class UploadConsistencyTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.override_media = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.override_media.enable()
        self.user = get_user_model().objects.create_user(
            username="upload_owner",
            password="SenhaForte123",
        )
        self.client.force_login(self.user)
        self.dataframe = pd.DataFrame(
            {
                "logradouro": ["Rua Teste"],
                "numero_logradouro": [10],
            }
        )

    def tearDown(self):
        self.override_media.disable()
        self.media_directory.cleanup()

    def _upload(self):
        return self.client.post(
            reverse("upload_file"),
            {
                "arquivo": SimpleUploadedFile(
                    "acidentes.csv",
                    b"logradouro;numero_logradouro\nRua Teste;10\n",
                    content_type="text/csv",
                ),
            },
        )

    def _stored_files(self):
        return {
            path.relative_to(self.media_directory.name).as_posix()
            for path in Path(self.media_directory.name).rglob("*")
            if path.is_file()
        }

    @patch("analytics.services.file_loader.run_preprocessing")
    @patch("analytics.services.file_loader.load_dataframe")
    def test_successful_upload_keeps_dataset_original_and_parquet(
        self,
        mock_load_dataframe,
        mock_run_preprocessing,
    ):
        mock_load_dataframe.return_value = self.dataframe
        mock_run_preprocessing.return_value = self.dataframe.copy()

        response = self._upload()

        self.assertRedirects(response, reverse("home"))
        dataset = Dataset.objects.get(usuario=self.user)
        self.assertTrue(Path(dataset.arquivo.path).exists())
        self.assertTrue(Path(dataset.resultado_processado.path).exists())
        mock_load_dataframe.assert_called_once()
        self.assertNotIn("preview_data", self.client.session)

    def test_review_without_legacy_preview_renders_empty_state(self):
        response = self.client.get(reverse("review_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["records"], [])
        self.assertContains(response, "Nenhum registro disponível")

    @patch(
        "analytics.services.file_loader.run_preprocessing",
        side_effect=RuntimeError("falha simulada"),
    )
    @patch("analytics.services.file_loader.load_dataframe")
    def test_preprocessing_failure_removes_incomplete_dataset_and_files(
        self,
        mock_load_dataframe,
        mock_run_preprocessing,
    ):
        mock_load_dataframe.return_value = self.dataframe

        response = self._upload()

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Dataset.objects.filter(usuario=self.user).exists())
        self.assertEqual(self._stored_files(), set())

    @patch("analytics.services.file_loader.load_dataframe")
    def test_parquet_write_failure_removes_created_orphan(self, mock_load_dataframe):
        mock_load_dataframe.return_value = self.dataframe

        def write_then_fail(dataframe, path):
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"parquet parcial")
            raise RuntimeError("falha após criar o arquivo")

        with patch(
            "analytics.persistence.datasets.save_dataframe_as_parquet",
            side_effect=write_then_fail,
        ):
            response = self._upload()

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Dataset.objects.filter(usuario=self.user).exists())
        self.assertEqual(self._stored_files(), set())

    @patch(
        "analytics.services.file_loader.run_preprocessing",
        side_effect=RuntimeError("falha simulada"),
    )
    @patch("analytics.services.file_loader.load_dataframe")
    def test_failed_upload_preserves_other_dataset_files(
        self,
        mock_load_dataframe,
        mock_run_preprocessing,
    ):
        mock_load_dataframe.return_value = self.dataframe
        other_user = get_user_model().objects.create_user(
            username="other_upload_owner",
            password="SenhaForte123",
        )
        other_dataset = DatasetService.create_from_upload(
            usuario=other_user,
            arquivo=SimpleUploadedFile(
                "acidentes.csv",
                b"logradouro\nOutro\n",
                content_type="text/csv",
            ),
            quantidade_registros=1,
        )
        other_dataset = DatasetService.save_processed_dataframe(
            other_dataset,
            pd.DataFrame({"logradouro": ["Outro"]}),
        )
        other_original = Path(other_dataset.arquivo.path)
        other_parquet = Path(other_dataset.resultado_processado.path)

        response = self._upload()

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Dataset.objects.count(), 1)
        self.assertTrue(Dataset.objects.filter(id=other_dataset.id).exists())
        self.assertTrue(other_original.exists())
        self.assertTrue(other_parquet.exists())


class DatasetRecordEditingTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.override_media = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.override_media.enable()
        self.user = get_user_model().objects.create_user(
            username="record_editor",
            password="SenhaForte123",
        )
        self.client.force_login(self.user)
        self.record_id = str(uuid4())
        self.dataset = self._create_dataset(
            self.user,
            "rua teste",
            self.record_id,
        )

    def tearDown(self):
        self.override_media.disable()
        self.media_directory.cleanup()

    def _create_dataset(self, user, logradouro_limpo, record_id=None):
        record_id = record_id or str(uuid4())
        dataset = DatasetService.create_from_upload(
            usuario=user,
            arquivo=SimpleUploadedFile(
                "registros.csv",
                b"logradouro\nRua Teste\n",
                content_type="text/csv",
            ),
            quantidade_registros=1,
        )
        return DatasetService.save_processed_dataframe(
            dataset,
            pd.DataFrame(
                {
                    "id_registro": [record_id],
                    "logradouro": ["Rua Teste"],
                    "logradouro_limpo": [logradouro_limpo],
                    "numero_logradouro": [10.0],
                    "logradouro_canonico": [""],
                    "correcao_manual_aplicada": [False],
                }
            ),
        )

    def _edit(self, updates, **extra_payload):
        payload = {
            "id_registro": self.record_id,
            "updates": updates,
            "note": "ajuste auditado",
            **extra_payload,
        }
        return self.client.post(
            reverse("dataset_update_record", args=[self.dataset.id]),
            data=payload,
            content_type="application/json",
        )

    def test_authenticated_user_is_recorded_as_audit_author(self):
        response = self._edit({"numero_logradouro": 20})

        self.assertEqual(response.status_code, 200)
        audit = DatasetRecordAudit.objects.get(dataset=self.dataset)
        self.assertEqual(audit.usuario, self.user)

    def test_client_author_cannot_spoof_audit_or_correction_author(self):
        response = self._edit(
            {"logradouro_canonico": "Rua Teste Oficial"},
            autor="usuario_forjado",
        )

        self.assertEqual(response.status_code, 200)
        record_audit = DatasetRecordAudit.objects.get(dataset=self.dataset)
        correction = AddressCorrection.objects.get(
            logradouro_limpo="rua teste"
        )
        correction_audit = CorrectionAudit.objects.get(correction=correction)
        self.assertEqual(record_audit.usuario, self.user)
        self.assertEqual(correction.autor, str(self.user))
        self.assertEqual(correction_audit.autor, str(self.user))

    def test_successful_edit_changes_parquet_and_creates_audit(self):
        response = self._edit({"numero_logradouro": 25})

        self.assertEqual(response.status_code, 200)
        dataframe = DatasetService.load_processed_dataframe(self.dataset)
        self.assertEqual(dataframe.loc[0, "numero_logradouro"], 25.0)
        self.assertTrue(
            DatasetRecordAudit.objects.filter(
                dataset=self.dataset,
                id_registro=self.record_id,
                field_name="numero_logradouro",
                previous_value="10.0",
                new_value="25.0",
                usuario=self.user,
            ).exists()
        )

    def test_audit_failure_restores_original_parquet(self):
        with patch(
            "analytics.persistence.datasets.DatasetRecordAudit.objects.create",
            side_effect=RuntimeError("falha simulada na auditoria"),
        ):
            response = self._edit({"numero_logradouro": 30})

        self.assertEqual(response.status_code, 500)
        dataframe = DatasetService.load_processed_dataframe(self.dataset)
        self.assertEqual(dataframe.loc[0, "numero_logradouro"], 10.0)
        self.assertFalse(
            DatasetRecordAudit.objects.filter(dataset=self.dataset).exists()
        )

    def test_correction_audit_failure_restores_parquet_and_database(self):
        with patch(
            "analytics.persistence.corrections._create_audit_entry",
            side_effect=RuntimeError("falha simulada na auditoria da correção"),
        ):
            response = self._edit(
                {"logradouro_canonico": "Rua Teste Oficial"}
            )

        self.assertEqual(response.status_code, 500)
        dataframe = DatasetService.load_processed_dataframe(self.dataset)
        self.assertEqual(dataframe.loc[0, "logradouro_canonico"], "")
        self.assertFalse(
            DatasetRecordAudit.objects.filter(dataset=self.dataset).exists()
        )
        self.assertFalse(
            AddressCorrection.objects.filter(
                logradouro_limpo="rua teste"
            ).exists()
        )
        self.assertFalse(CorrectionAudit.objects.exists())

    def test_user_cannot_edit_another_users_dataset(self):
        other_user = get_user_model().objects.create_user(
            username="other_record_owner",
            password="SenhaForte123",
        )
        self.client.force_login(other_user)

        response = self._edit({"numero_logradouro": 40})

        self.assertEqual(response.status_code, 404)
        dataframe = DatasetService.load_processed_dataframe(self.dataset)
        self.assertEqual(dataframe.loc[0, "numero_logradouro"], 10.0)
        self.assertFalse(
            DatasetRecordAudit.objects.filter(dataset=self.dataset).exists()
        )

    def test_approved_address_correction_remains_global(self):
        response = self._edit(
            {"logradouro_canonico": "Rua Teste Oficial"}
        )
        self.assertEqual(response.status_code, 200)

        other_user = get_user_model().objects.create_user(
            username="future_dataset_owner",
            password="SenhaForte123",
        )
        other_dataset = self._create_dataset(
            other_user,
            "rua teste",
        )
        other_dataframe = DatasetService.load_processed_dataframe(other_dataset)
        corrected = apply_manual_corrections(other_dataframe)

        self.assertEqual(
            corrected.loc[0, "logradouro_canonico"],
            "Rua Teste Oficial",
        )
        self.assertTrue(corrected.loc[0, "correcao_manual_aplicada"])


class DatasetFileFlowTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.override_media = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.override_media.enable()
        self.user = get_user_model().objects.create_user(
            username="file_flow_owner",
            password="SenhaForte123",
        )
        self.client.force_login(self.user)

    def tearDown(self):
        self.override_media.disable()
        self.media_directory.cleanup()

    def _create_dataset(self, dataframe, filename="detalhe.csv"):
        dataset = DatasetService.create_from_upload(
            usuario=self.user,
            arquivo=SimpleUploadedFile(
                filename,
                b"logradouro\nRua Teste\n",
                content_type="text/csv",
            ),
            quantidade_registros=len(dataframe),
        )
        return DatasetService.save_processed_dataframe(dataset, dataframe)

    def _detail_dataframe(self):
        return pd.DataFrame(
            {
                "id_registro": [str(uuid4())],
                "logradouro": ["Rua Teste"],
                "logradouro_limpo": ["rua teste"],
                "numero_logradouro": [10],
                "logradouro_sugerido": ["rua teste"],
                "logradouro_canonico": ["Rua Teste"],
                "correcao_manual_aplicada": [True],
            }
        )

    def test_detail_with_all_expected_columns(self):
        dataset = self._create_dataset(self._detail_dataframe())

        response = self.client.get(
            reverse("dataset_detail", args=[dataset.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["load_error"])
        self.assertEqual(
            response.context["page_obj"].object_list[0]["numero_logradouro"],
            10,
        )

    def test_detail_without_optional_numero_logradouro(self):
        dataframe = self._detail_dataframe().drop(
            columns=["numero_logradouro"]
        )
        dataset = self._create_dataset(dataframe)

        response = self.client.get(
            reverse("dataset_detail", args=[dataset.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["load_error"])
        record = response.context["page_obj"].object_list[0]
        self.assertNotIn("numero_logradouro", record)

    def test_load_small_csv_from_memory(self):
        uploaded_file = SimpleUploadedFile(
            "pequeno.csv",
            "logradouro;numero\nRua São João;12\n".encode("utf-8"),
            content_type="text/csv",
        )

        dataframe = load_dataframe(uploaded_file)

        self.assertEqual(dataframe.loc[0, "logradouro"], "Rua São João")
        self.assertEqual(dataframe.loc[0, "numero"], 12)

    def test_load_csv_from_temporary_uploaded_file(self):
        content = "logradouro;numero\nRua São João;12\n".encode("cp1252")
        uploaded_file = TemporaryUploadedFile(
            "temporario.csv",
            "text/csv",
            len(content),
            "cp1252",
        )
        try:
            uploaded_file.write(content)
            uploaded_file.seek(0)

            dataframe = load_dataframe(uploaded_file)
        finally:
            uploaded_file.close()

        self.assertEqual(dataframe.loc[0, "logradouro"], "Rua São João")
        self.assertEqual(dataframe.loc[0, "numero"], 12)

    def test_download_returns_valid_xlsx(self):
        dataset = self._create_dataset(
            self._detail_dataframe(),
            filename="relatorio.csv",
        )

        response = self.client.get(
            reverse("dataset_download", args=[dataset.id])
        )
        content = b"".join(response.streaming_content)
        response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        exported = pd.read_excel(BytesIO(content))
        self.assertEqual(exported.loc[0, "logradouro"], "Rua Teste")

    def test_download_closes_spooled_temporary_file(self):
        dataset = self._create_dataset(self._detail_dataframe())
        created_files = []
        real_spooled_file = tempfile.SpooledTemporaryFile

        def create_spooled_file(*args, **kwargs):
            temporary_file = real_spooled_file(*args, **kwargs)
            created_files.append(temporary_file)
            return temporary_file

        with patch(
            "analytics.views.datasets.tempfile.SpooledTemporaryFile",
            side_effect=create_spooled_file,
        ):
            response = self.client.get(
                reverse("dataset_download", args=[dataset.id])
            )
            b"".join(response.streaming_content)
            response.close()

        self.assertEqual(len(created_files), 1)
        self.assertTrue(created_files[0].closed)


class ProcessUploadTests(SimpleTestCase):
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
