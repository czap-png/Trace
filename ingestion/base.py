from abc import ABC, abstractmethod
from db.client import get_connection

class BasePipeline(ABC):
    """
    Every ingestion pipeline inherits from this.
    It enforces a consistent structure: fetch, normalise, upsert.
    """

    source_name: str = ""

    def run(self):
        print(f"[{self.source_name}] Starting pipeline...")
        raw = self.fetch()
        print(f"[{self.source_name}] Fetched {len(raw)} records.")
        normalised = self.normalise(raw)
        print(f"[{self.source_name}] Normalised {len(normalised)} entities.")
        with get_connection() as conn:
            self.upsert(conn, normalised)
        print(f"[{self.source_name}] Done.")

    @abstractmethod
    def fetch(self) -> list:
        """Pull raw data from the source. Return a list of raw records."""
        pass

    @abstractmethod
    def normalise(self, raw: list) -> list:
        """Transform raw records into a list of dicts ready for the DB."""
        pass

    @abstractmethod
    def upsert(self, conn, normalised: list):
        """Write normalised records to Postgres."""
        pass