from rest_framework.response import Response
from rest_framework.decorators import api_view
import math

# Old Tax Regime Calculation
def calculate_old_regime_tax(gross_income, deductions):
    standard_deduction = 50000
    total_deductions = standard_deduction + sum(deductions.values())
    taxable_income = max(0, gross_income - total_deductions)

    tax = 0
    if taxable_income <= 250000:
        tax = 0
    elif taxable_income <= 500000:
        tax = (taxable_income - 250000) * 0.05
    elif taxable_income <= 1000000:
        tax = 12500 + (taxable_income - 500000) * 0.20
    else:
        tax = 12500 + 100000 + (taxable_income - 1000000) * 0.30

    cess = tax * 0.04
    return round(tax + cess, 2)

# New Tax Regime Calculation
def calculate_new_regime_tax(gross_income):
    standard_deduction = 75000
    taxable_income = gross_income - standard_deduction

    tax = 0
    if taxable_income <= 300000:
        tax = 0
    elif taxable_income <= 700000:
        tax = (taxable_income - 300000) * 0.05
    elif taxable_income <= 1000000:
        tax = 20000 + (taxable_income - 700000) * 0.10
    elif taxable_income <= 1200000:
        tax = 20000 + 30000 + (taxable_income - 1000000) * 0.15
    elif taxable_income <= 1500000:
        tax = 20000 + 30000 + 30000 + (taxable_income - 1200000) * 0.20
    else:
        tax = 20000 + 30000 + 30000 + 60000 + (taxable_income - 1500000) * 0.30

    cess = tax * 0.04
    return round(tax + cess, 2)

# API View
@api_view(['POST'])
def calculate_tax(request):
    data = request.data
    gross_income = float(data.get('gross_income', 0))
    deductions = {
        "80C": float(data.get('deduction_80c', 0)),
        "80D": float(data.get('deduction_80d', 0)),
        "80E": float(data.get('deduction_80e', 0)),
        "80G": float(data.get('deduction_80g', 0)),
        "80TTA": float(data.get('deduction_80tta', 0)),
        "HomeLoan": float(data.get('home_loan_interest', 0)),
        "NPS": float(data.get('nps_contribution', 0)),
    }

    old_tax = calculate_old_regime_tax(gross_income, deductions)
    new_tax = calculate_new_regime_tax(gross_income)

    return Response({
        "Old Regime Tax": old_tax,
        "New Regime Tax": new_tax,
        "Recommended Regime": "New" if new_tax < old_tax else "Old" if old_tax>new_tax else"Zero Tax"
    })
