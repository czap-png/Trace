from ingestion.companies_house import CompaniesHousePipeline
from ingestion.open_sanctions import OpenSanctionsPipeline

if __name__ == "__main__":
    CompaniesHousePipeline().run()
    OpenSanctionsPipeline().run()