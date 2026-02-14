import requests
import pandas as pd
from typing import Optional, Dict, List

class FiscalAIClient:
    """Cliente para interactuar con Fiscal.AI API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.fiscal.ai"
        self.headers = {"X-Api-Key": api_key}
    
    def get_companies_list(self, page_size: int = 1000) -> List[Dict]:
        """Obtiene lista de todas las empresas"""
        response = requests.get(
            f"{self.base_url}/v2/companies-list",
            headers=self.headers,
            params={"pageSize": page_size}
        )
        return response.json()
    
    def get_cash_flow_statement(self, ticker: str, period_type: str = "annual") -> Dict:
        """Obtiene estado de flujos de efectivo"""
        response = requests.get(
            f"{self.base_url}/v1/company/financials/cash-flow-statement/standardized",
            headers=self.headers,
            params={"ticker": ticker, "periodType": period_type, "currency": "USD"}
        )
        return response.json()
    
    def get_balance_sheet(self, ticker: str, period_type: str = "latest") -> Dict:
        """Obtiene balance general"""
        response = requests.get(
            f"{self.base_url}/v1/company/financials/balance-sheet/standardized",
            headers=self.headers,
            params={"ticker": ticker, "periodType": period_type, "currency": "USD"}
        )
        return response.json()
    
    def get_ratios(self, ticker: str, period_type: str = "latest") -> Dict:
        """Obtiene ratios financieros"""
        response = requests.get(
            f"{self.base_url}/v1/company/ratios",
            headers=self.headers,
            params={"ticker": ticker, "periodType": period_type}
        )
        return response.json()
    
    def get_stock_prices(self, ticker: str, page_size: int = 1) -> Dict:
        """Obtiene precios de acciones"""
        response = requests.get(
            f"{self.base_url}/v1/company/stock-prices",
            headers=self.headers,
            params={"ticker": ticker, "pageSize": page_size}
        )
        return response.json()
