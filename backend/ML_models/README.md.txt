# ML Training - Stock Price Prediction (TrackEx)

This module trains stock price prediction models using a hybrid of Attention-based CNN + BiLSTM + LSTM + XGBoost.

---

## 📂 File Structure

- `train_models.py` – Training pipeline for multiple stocks
- `requirements_ml.txt` – Dependencies for training
- Output folders (ignored from Git):  
  - `../models/` – Saved `.h5`, `.pkl`, and `.pkl` models  
  - `../data/` – Raw downloaded stock data  
  - `../predictions/` – Prediction CSVs for each stock

---

## 🛠️ Setup & Usage

1. Install required packages:
   ```bash
   pip install -r requirements_ml.txt
