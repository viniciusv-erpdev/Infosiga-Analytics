from io import BytesIO
from unittest.mock import patch

import pandas as pd
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase

from analytics.services.file_loader import process_upload


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
