import json
import logging
from typing import Any, Dict, Optional
import requests


class DSGVO_LLM:
    """Lokale KI-Schnittstelle zur DSGVO-konformen Generierung von geodätischen Fachberichten.

    Kommuniziert direkt mit einer lokal gehosteten Ollama Instanz (Llama-3), ohne
    sensible Vermessungs- und PII-Daten an externe Cloud-Anbieter zu übertragen.
    """

    def __init__(
        self,
        host_url: str = "http://localhost:11434",
        model_name: str = "llama3",
    ) -> None:
        """Initialisiert die Verbindungsparameter zur Ollama API."""
        self.host_url = host_url.rstrip("/")
        self.generate_endpoint = f"{self.host_url}/api/generate"
        self.tags_endpoint = f"{self.host_url}/api/tags"
        self.model_name = model_name
        self.logger = logging.getLogger(self.__class__.__name__)

    def is_available(self) -> bool:
        """Prüft umgehend, ob die lokale Ollama-Instanz erreichbar ist."""
        try:
            response = requests.get(self.tags_endpoint, timeout=3.0)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate_fachbericht(
        self, project_data_dict: Dict[str, Any], timeout: int = 60
    ) -> str:
        """Generiert einen DIN 18716 konformen Geodäsie- und Trassierungsfachbericht."""
        system_instructions = (
            "Du bist ein leitender Prüfingenieur für Geodäsie und Verkehrswegebau in Nordrhein-Westfalen. "
            "Erstelle auf Basis der übergebenen Projektdaten einen präzisen, hochprofessionellen "
            "ingenieurtechnischen Fachbericht gemäß DIN 18716 und REB 22.013.\n"
            "Verwende striktes deutsches Fachdeutsch. Strukturierung:\n"
            "1. Zusammenfassung & Projektkontext\n"
            "2. Geodätische Grundlagen & Bezugssysteme\n"
            "3. Erdmengenberechnung & Volumennachweis\n"
            "4. Bewertung, Genauigkeitsklasse & Freigabeentscheidung."
        )

        formatted_data_json = json.dumps(
            project_data_dict, indent=2, ensure_ascii=False
        )

        user_prompt = (
            f"{system_instructions}\n\n"
            f"PROJEKT-DATENSET (JSON):\n```json\n{formatted_data_json}\n```\n\n"
            f"Erstelle nun den vollständigen, revisionssicheren Fachbericht:"
        )

        payload = {
            "model": self.model_name,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_ctx": 4096,
            },
        }

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )

            if response.status_code == 200:
                result_json = response.json()
                report_text = result_json.get("response", "").strip()
                if report_text:
                    return report_text
                return "FEHLER: Die lokale LLM-Antwort enthielt keinen Text."
            else:
                return (
                    f"FEHLER: LLM-Server antwortete mit Statuscode {response.status_code}. "
                    f"Details: {response.text}"
                )

        except requests.exceptions.Timeout:
            self.logger.error("Zeitüberschreitung bei der Anfrage an das lokale LLM.")
            return (
                "FEHLER: Zeitüberschreitung (Timeout) bei der Kommunikation mit Ollama. "
                "Bitte stellen Sie sicher, dass das Modell geladen ist."
            )
        except requests.exceptions.ConnectionError:
            self.logger.error("Verbindung zum Ollama-Dienst fehlgeschlagen.")
            return (
                "FEHLER: Lokaler LLM-Dienst nicht erreichbar unter http://localhost:11434. "
                "Bitte starten Sie Ollama ('ollama serve')."
            )
        except Exception as err:
            self.logger.error(f"Unerwarteter LLM-Fehler: {str(err)}")
            return f"FEHLER: Bei der Erstellung des Fachberichts ist ein Fehler aufgetreten: {str(err)}"