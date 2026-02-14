import pandas as pd
import numpy as np
from fiscal_api import FiscalAIClient

class DCFCalculator:
    """Motor de cálculo DCF"""
    
    def __init__(self, fiscal_client: FiscalAIClient):
        self.client = fiscal_client
    
    def calculate_historical_fcf(self, ticker: str) -> pd.DataFrame:
        """Calcula FCF histórico"""
        cf_data = self.client.get_cash_flow_statement(ticker)
        
        fcf_history = []
        for period in cf_data.get('periods', []):
            operating_cf = period.get('operating_cash_flow', 0)
            capex = period.get('capital_expenditure', 0)
            fcf = operating_cf - abs(capex)
            
            fcf_history.append({
                'year': period.get('fiscal_year'),
                'fcf': fcf
            })
        
        return pd.DataFrame(fcf_history)
    
    def project_fcf(self, historical_fcf: pd.DataFrame, 
                    growth_rate: float = 0.05, years: int = 5):
        """Proyecta FCF futuro"""
        if historical_fcf.empty:
            return []
        
        last_fcf = historical_fcf['fcf'].iloc[-1]
        projections = []
        
        for year in range(1, years + 1):
            projected_fcf = last_fcf * ((1 + growth_rate) ** year)
            projections.append(projected_fcf)
        
        return projections
    
    def calculate_wacc(self, ticker: str, risk_free_rate: float = 0.04, 
                       market_return: float = 0.10) -> float:
        """Calcula WACC"""
        try:
            bs_data = self.client.get_balance_sheet(ticker)
            ratios_data = self.client.get_ratios(ticker)
            
            bs_latest = bs_data['periods'][0]
            ratios_latest = ratios_data['periods'][0]
            
            total_debt = bs_latest.get('total_debt', 0)
            equity = bs_latest.get('total_equity', 1)
            beta = ratios_latest.get('beta', 1.0)
            
            # CAPM
            cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
            
            # Costo de deuda simplificado
            cost_of_debt = 0.05
            tax_rate = 0.21
            
            # Pesos
            total_value = total_debt + equity
            if total_value == 0:
                return cost_of_equity
            
            weight_debt = total_debt / total_value
            weight_equity = equity / total_value
            
            # WACC
            wacc = (weight_equity * cost_of_equity) + \
                   (weight_debt * cost_of_debt * (1 - tax_rate))
            
            return wacc
        except Exception as e:
            return 0.10
    
    def calculate_dcf_value(self, projected_fcf, wacc: float, 
                           terminal_growth: float = 0.025):
        """Calcula valor DCF"""
        if not projected_fcf or wacc <= terminal_growth:
            return 0, 0
        
        # Descontar FCF proyectados
        pv_fcf = []
        for year, fcf in enumerate(projected_fcf, 1):
            pv = fcf / ((1 + wacc) ** year)
            pv_fcf.append(pv)
        
        # Valor Terminal
        last_fcf = projected_fcf[-1]
        terminal_value = (last_fcf * (1 + terminal_growth)) / (wacc - terminal_growth)
        pv_terminal = terminal_value / ((1 + wacc) ** len(projected_fcf))
        
        # Valor Empresa
        enterprise_value = sum(pv_fcf) + pv_terminal
        
        return enterprise_value, pv_terminal
    
    def calculate_equity_value(self, ticker: str, enterprise_value: float) -> float:
        """Calcula valor de equity"""
        try:
            bs_data = self.client.get_balance_sheet(ticker)
            bs_latest = bs_data['periods'][0]
            
            cash = bs_latest.get('cash_and_equivalents', 0)
            debt = bs_latest.get('total_debt', 0)
            
            equity_value = enterprise_value + cash - debt
            return max(equity_value, 0)
        except:
            return enterprise_value
    
    def screen_opportunities(self, min_upside: float = 0.20, 
                            max_companies: int = 50) -> pd.DataFrame:
        """Screening de oportunidades"""
        try:
            companies_response = self.client.get_companies_list(page_size=max_companies)
            
            # La API devuelve un diccionario, necesitamos extraer la lista
            if isinstance(companies_response, dict):
                companies = companies_response.get('data', [])
            elif isinstance(companies_response, list):
                companies = companies_response
            else:
                return pd.DataFrame()
            
            opportunities = []
            
            # Limitar el número de empresas a analizar
            companies_to_analyze = companies[:min(len(companies), max_companies)]
            
            for company in companies_to_analyze:
                ticker = company.get('ticker')
                if not ticker:
                    continue
                
                try:
                    print(f"\n📊 Analizando {ticker}...")
                    
                    # Calcular DCF
                    historical_fcf = self.calculate_historical_fcf(ticker)
                    if historical_fcf.empty:
                        print(f"  ⚠️ {ticker}: No hay datos históricos de FCF")
                        continue
                    
                    print(f"  ✓ FCF histórico obtenido: {len(historical_fcf)} períodos")
                    
                    projected_fcf = self.project_fcf(historical_fcf)
                    print(f"  ✓ FCF proyectado: {len(projected_fcf)} años")
                    
                    wacc = self.calculate_wacc(ticker)
                    print(f"  ✓ WACC: {wacc:.2%}")
                    
                    enterprise_value, _ = self.calculate_dcf_value(projected_fcf, wacc)
                    print(f"  ✓ Valor Empresa: ${enterprise_value/1e9:.2f}B")
                    
                    equity_value = self.calculate_equity_value(ticker, enterprise_value)
                    print(f"  ✓ Valor Equity: ${equity_value/1e9:.2f}B")
                    
                    # Obtener precio actual
                    price_data = self.client.get_stock_prices(ticker)
                    if not price_data.get('prices'):
                        print(f"  ⚠️ {ticker}: No hay datos de precio")
                        continue
                    
                    current_price = price_data['prices'][0].get('close', 0)
                    print(f"  ✓ Precio actual: ${current_price:.2f}")
                    
                    # Calcular upside
                    shares_outstanding = company.get('shares_outstanding', 1)
                    if shares_outstanding == 0:
                        print(f"  ⚠️ {ticker}: Shares outstanding = 0")
                        continue
                    
                    intrinsic_price = equity_value / shares_outstanding
                    market_cap = current_price * shares_outstanding
                    upside = (equity_value - market_cap) / market_cap if market_cap > 0 else 0
                    
                    print(f"  ✓ Precio intrínseco: ${intrinsic_price:.2f}")
                    print(f"  ✓ Market cap: ${market_cap/1e9:.2f}B")
                    print(f"  💰 UPSIDE: {upside*100:.2f}%")
                    
                    if upside >= min_upside:
                        print(f"  ✅ {ticker} CUMPLE el filtro de upside!")
                        opportunities.append({
                            'ticker': ticker,
                            'company_name': company.get('name', ticker),
                            'current_price': current_price,
                            'intrinsic_value': intrinsic_price,
                            'market_cap': market_cap / 1e9,
                            'upside_pct': upside * 100
                        })
                    else:
                        print(f"  ❌ {ticker} NO cumple (necesita {min_upside*100:.1f}%, tiene {upside*100:.2f}%)")
                    
                    # Calcular upside
                    shares_outstanding = company.get('shares_outstanding', 1)
                    if shares_outstanding == 0:
                        continue
                    
                    intrinsic_price = equity_value / shares_outstanding
                    market_cap = current_price * shares_outstanding
                    upside = (equity_value - market_cap) / market_cap if market_cap > 0 else 0
                    
                    if upside >= min_upside:
                        opportunities.append({
                            'ticker': ticker,
                            'company_name': company.get('name', ticker),
                            'current_price': current_price,
                            'intrinsic_value': intrinsic_price,
                            'market_cap': market_cap / 1e9,
                            'upside_pct': upside * 100
                        })
                    
                except Exception as e:
                    print(f"Error analyzing {ticker}: {e}")
                    continue
            
            df = pd.DataFrame(opportunities)
            if not df.empty:
                df = df.sort_values('upside_pct', ascending=False)
            
            return df
            
        except Exception as e:
            print(f"Error general en screening: {e}")
            return pd.DataFrame()
