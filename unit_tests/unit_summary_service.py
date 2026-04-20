import unittest
from types import SimpleNamespace

from text_processing import SummaryService


class FakeConfigManager:
    def __init__(self, values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)

    def get_int(self, key, default=0):
        return int(self.values.get(key, default))

    def get_float(self, key, default=0.0):
        return float(self.values.get(key, default))


class FakeChatEndpoint:
    def __init__(self, response_text=None, error=None):
        self.response_text = response_text
        self.error = error
        self.calls = []
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.response_text)
                )
            ]
        )


class FakeCompletionEndpoint:
    def __init__(self, response_text=None, error=None):
        self.response_text = response_text
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(text=self.response_text)
            ]
        )


class SummaryServiceEndpointTests(unittest.TestCase):
    def _build_service(self, engine, chat_response=None, completion_response=None, chat_error=None, completion_error=None):
        config = FakeConfigManager(
            {
                "OPENAI_API_KEY": "",
                "OPENAI_ENGINE": engine,
                "MAX_SUMMARY_TOKENS": 120,
                "SUMMARY_TEMPERATURE": 0.2,
            }
        )
        service = SummaryService(config)
        service.enabled = True
        service.client = SimpleNamespace(
            chat=FakeChatEndpoint(response_text=chat_response, error=chat_error),
            completions=FakeCompletionEndpoint(response_text=completion_response, error=completion_error),
        )
        return service

    def test_instruct_model_uses_legacy_completions_endpoint(self):
        service = self._build_service(
            engine="gpt-3.5-turbo-instruct",
            completion_response="Resumen legacy",
        )

        summary = service.summarize_text("Texto de prueba", "es")

        self.assertEqual(summary, "Resumen legacy")
        self.assertEqual(len(service.client.chat.calls), 0)
        self.assertEqual(len(service.client.completions.calls), 1)
        self.assertEqual(service.client.completions.calls[0]["model"], "gpt-3.5-turbo-instruct")

    def test_chat_model_uses_chat_completions_endpoint(self):
        service = self._build_service(
            engine="gpt-4o-mini",
            chat_response="Resumen chat",
        )

        summary = service.summarize_text("Texto de prueba", "es")

        self.assertEqual(summary, "Resumen chat")
        self.assertEqual(len(service.client.chat.calls), 1)
        self.assertEqual(len(service.client.completions.calls), 0)
        self.assertEqual(service.client.chat.calls[0]["model"], "gpt-4o-mini")

    def test_retries_with_completions_when_chat_endpoint_is_rejected(self):
        service = self._build_service(
            engine="mi-modelo-personalizado",
            chat_error=Exception(
                "This is not a chat model and thus not supported in the v1/chat/completions endpoint. "
                "Did you mean to use v1/completions?"
            ),
            completion_response="Resumen recuperado",
        )

        summary = service.summarize_text("Texto de prueba", "es")

        self.assertEqual(summary, "Resumen recuperado")
        self.assertEqual(len(service.client.chat.calls), 1)
        self.assertEqual(len(service.client.completions.calls), 1)


if __name__ == "__main__":
    unittest.main()
