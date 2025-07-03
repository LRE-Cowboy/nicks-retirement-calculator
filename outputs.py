# Standard library imports
from typing import Dict, Any, List
import json

# Third-party imports
import plotly.graph_objs as go
import streamlit as st
import numpy as np

# Local imports
from calculations import project_retirement, monte_carlo_simulation


def plot_net_worth_vs_time(projection: Dict[str, Any]) -> None:
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=projection["ages"], y=projection["net_worth"], mode="lines", name="Net Worth"))
	fig.update_layout(title="Net Worth vs Time", xaxis_title="Age (years)", yaxis_title="Net Worth ($)")
	st.plotly_chart(fig)


def plot_income_vs_expenses(projection: Dict[str, Any]) -> None:
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=projection["ages"], y=projection["income"], mode="lines", name="Income/Withdrawal"))
	fig.add_trace(go.Scatter(x=projection["ages"], y=projection["expenses"], mode="lines", name="Expenses"))
	fig.update_layout(title="Income and Expenses vs Time", xaxis_title="Age (years)", yaxis_title="Amount ($)")
	st.plotly_chart(fig)


def plot_income_vs_expenses_real(projection: Dict[str, Any], inputs: Dict[str, Any]) -> None:
	"""Plot income and expenses vs time, normalized to current day dollars. Retirement years are normalized from retirement_age."""
	ages = projection["ages"]
	income = projection["income"]
	expenses = projection["expenses"]
	retirement_age = projection["retirement_age"]
	# Compute cumulative inflation for each year, but for retirement years, inflation is from retirement_age
	cumulative_inflation = np.ones(len(ages))
	for i in range(1, len(ages)):
		if ages[i] < retirement_age:
			cumulative_inflation[i] = cumulative_inflation[i-1] * (1 + inputs["inflation"] / 100)
		else:
			cumulative_inflation[i] = (1 + inputs["inflation"] / 100) ** (ages[i] - retirement_age)
	income_real = income / cumulative_inflation
	expenses_real = expenses / cumulative_inflation
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=ages, y=income_real, mode="lines", name="Income/Withdrawal (Real $)"))
	fig.add_trace(go.Scatter(x=ages, y=expenses_real, mode="lines", name="Expenses (Real $)"))
	fig.update_layout(title="Income and Expenses vs Time (Current Day Dollars)", xaxis_title="Age (years)", yaxis_title="Amount (Current $)")
	st.plotly_chart(fig)


def export_simulation_details(inputs: Dict[str, Any], results: Dict[str, Any], filename: str = "simulation_export.txt") -> None:
	"""
	Export all key assumptions and projected outcomes to a text file.
	"""
	with open(filename, "w") as f:
		f.write("Retirement Calculator Simulation Export\n")
		f.write("=" * 50 + "\n\n")
		
		f.write("INPUT ASSUMPTIONS:\n")
		f.write("-" * 20 + "\n")
		for k, v in inputs.items():
			if k == "salary_upgrades" and v:
				f.write(f"  {k}: {v}\n")
			elif isinstance(v, (int, float)):
				f.write(f"  {k}: {v:,.2f}\n")
			else:
				f.write(f"  {k}: {v}\n")
		
		f.write("\n\nPROJECTED OUTCOMES:\n")
		f.write("-" * 20 + "\n")
		for k, v in results.items():
			if isinstance(v, (int, float)):
				f.write(f"  {k}: {v:,.2f}\n")
			else:
				f.write(f"  {k}: {v}\n")
		
		f.write("\n\nMONTE CARLO SIMULATION RESULTS:\n")
		f.write("-" * 30 + "\n")
		f.write(f"  Success Rate: {results.get('success_rate', 0)*100:.1f}%\n")
		f.write(f"  Median Net Worth at Death: ${results.get('median_net_worth', 0):,.0f}\n")
		f.write(f"  10th Percentile Net Worth at Death: ${results.get('percentile_10_net_worth', 0):,.0f}\n")
		
		f.write("\n\nNOTES:\n")
		f.write("-" * 6 + "\n")
		f.write("- This simulation assumes no social security or pension income\n")
		f.write("- All amounts are in current dollars\n")
		f.write("- Monte Carlo simulation includes random variations in growth rates and inflation\n") 