from ingestion.companies_house import CompaniesHousePipeline
from ingestion.open_sanctions import OpenSanctionsPipeline
from ingestion.icij import ICIJPipeline

if __name__ == "__main__":
    CompaniesHousePipeline().run()
    OpenSanctionsPipeline().run()
    ICIJPipeline().run()