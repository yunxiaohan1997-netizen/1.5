"""
Payoff matrix loading and calculation functions.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Tuple

class PayoffMatrices:
    """Loads and manages payoff matrices for AM and MC."""
    
    def __init__(self, excel_path: str = None):
        """
        Load payoff matrices from Excel file.
        
        Args:
            excel_path: Path to the Excel file containing payoff matrices.
                       If None, tries multiple default locations.
        """
        if excel_path is None:
            # Try multiple possible locations
            possible_paths = [
                "/mnt/user-data/uploads/11_29.xlsx",  # Original location
                "11_29.xlsx",  # Project root
                "../11_29.xlsx",  # Parent directory
                "data/11_29.xlsx",  # Data subdirectory
                os.getenv("PAYOFF_MATRIX_PATH", "11_29.xlsx")  # From environment
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    excel_path = path
                    break
            
            if excel_path is None:
                raise FileNotFoundError(
                    "Could not find 11_29.xlsx in any of the expected locations. "
                    "Please set PAYOFF_MATRIX_PATH environment variable or place the file in the project root."
                )
        
        self.am_matrix, self.mc_matrix = self._load_matrices(excel_path)
        self._validate_matrices()
    
    def _load_matrices(self, excel_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load AM and MC payoff matrices from Excel.
        
        The Excel structure:
        - Sheet1 (AM payoffs): Row labels in Col 2, Data in Cols 3-28 (26 columns for MC=0-25)
        - Sheet2 (MC payoffs): Row labels in Col 3, Data in Cols 4-29 (26 columns for AM=0-25)
        - Data starts at row 4 (index 3 in both sheets)
        - 26x26 matrices (0-25 engineers)
        
        Note: The two sheets have slightly different structures!
        """
        # Load AM matrix (Sheet1)
        # Rows: AM investment (0-25), Columns: MC investment (0-25)
        df_am_raw = pd.read_excel(excel_path, sheet_name='Sheet1', header=None)
        am_matrix = df_am_raw.iloc[4:30, 3:29].values.astype(float)  # 26 rows, 26 cols
        
        # Load MC matrix (Sheet2)
        # Rows: MC investment (0-25), Columns: AM investment (0-25)
        df_mc_raw = pd.read_excel(excel_path, sheet_name='Sheet2', header=None)
        mc_matrix = df_mc_raw.iloc[4:30, 4:30].values.astype(float)  # 26 rows, 26 cols
        
        return am_matrix, mc_matrix
    
    def _validate_matrices(self):
        """Validate that matrices have correct dimensions."""
        assert self.am_matrix.shape == (26, 26), f"AM matrix should be 26x26, got {self.am_matrix.shape}"
        assert self.mc_matrix.shape == (26, 26), f"MC matrix should be 26x26, got {self.mc_matrix.shape}"
        assert not np.isnan(self.am_matrix).any(), "AM matrix contains NaN values"
        assert not np.isnan(self.mc_matrix).any(), "MC matrix contains NaN values"
    
    def get_am_payoff(self, am_investment: int, mc_investment: int) -> float:
        """
        Get AM's payoff for a given investment combination.
        
        Args:
            am_investment: AM engineers (0-25)
            mc_investment: MC engineers (0-25)
        
        Returns:
            AM's net payoff
        """
        if not (0 <= am_investment <= 25 and 0 <= mc_investment <= 25):
            raise ValueError(f"Investments must be 0-25. Got AM={am_investment}, MC={mc_investment}")
        
        return float(self.am_matrix[am_investment, mc_investment])
    
    def get_mc_payoff(self, am_investment: int, mc_investment: int) -> float:
        """
        Get MC's payoff for a given investment combination.
        
        Args:
            am_investment: AM engineers (0-25)
            mc_investment: MC engineers (0-25)
        
        Returns:
            MC's net payoff
        """
        if not (0 <= am_investment <= 25 and 0 <= mc_investment <= 25):
            raise ValueError(f"Investments must be 0-25. Got AM={am_investment}, MC={mc_investment}")
        
        # IMPORTANT: MC matrix is indexed as [MC_investment, AM_investment]
        return float(self.mc_matrix[am_investment, mc_investment])
    
    def calculate_round_outcomes(self, am_investment: int, mc_investment: int) -> dict:
        """
        Calculate complete outcomes for a round given both investments.
        
        Args:
            am_investment: AM engineers (0-25)
            mc_investment: MC engineers (0-25)
        
        Returns:
            Dictionary with payoffs and collective value
        """
        am_payoff = self.get_am_payoff(am_investment, mc_investment)
        mc_payoff = self.get_mc_payoff(am_investment, mc_investment)
        
        # Total welfare is sum of both payoffs
        total_welfare = am_payoff + mc_payoff
        
        return {
            "am_payoff": round(am_payoff, 2),
            "mc_payoff": round(mc_payoff, 2),
            "total_welfare": round(total_welfare, 2),
            "collective_value": round(total_welfare, 2)  # Same as total welfare in this formulation
        }
    
    def get_payoff_matrix_sample(self, agent: str) -> str:
        """
        Get a formatted sample of the payoff matrix for display to agents.
        Shows corners and middle values (not entire 26x26 to save tokens).
        
        Args:
            agent: "am" or "mc"
        
        Returns:
            Formatted string representation
        """
        matrix = self.am_matrix if agent.lower() == "am" else self.mc_matrix
        label = "Your" if agent else "Partner's"
        
        result = f"{label} payoffs (sample):\n"
        result += "        Partner: 0      5      10     15     20     25\n"
        
        for my_invest in [0, 5, 10, 15, 20, 25]:
            result += f"You {my_invest:2d}: "
            for partner_invest in [0, 5, 10, 15, 20, 25]:
                payoff = matrix[my_invest, partner_invest]
                result += f"{payoff:6.1f} "
            result += "\n"
        
        result += "\n(Showing sample values - full 26x26 matrix available)\n"
        return result
    
    def get_full_matrix_for_agent(self, agent: str) -> np.ndarray:
        """
        Get the full payoff matrix for an agent.
        Used in symmetric information mode.
        
        Args:
            agent: "am" or "mc"
        
        Returns:
            26x26 numpy array
        """
        return self.am_matrix if agent.lower() == "am" else self.mc_matrix


# Global instance (loaded once at startup)
_payoff_matrices = None

def get_payoff_matrices() -> PayoffMatrices:
    """Get the global PayoffMatrices instance."""
    global _payoff_matrices
    if _payoff_matrices is None:
        _payoff_matrices = PayoffMatrices()
    return _payoff_matrices
