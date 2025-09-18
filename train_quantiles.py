
"""
train_quantiles.py — Entrena modelos cuantílicos P10/P50/P90 y guarda artefactos:
- models/feature_columns.json
- models/preprocessor.pkl (ColumnTransformer)
- models/model_p10.pkl, models/model_p50.pkl, models/model_p90.pkl
- (opcional) models/shap_explainer.pkl
Usa vivienda_imputada.xlsx y columns.json (features) de tu repo original.
"""
import json, joblib, numpy as np, pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_XLS = 'data/vivienda_imputada.xlsx'
COLUMNS_JSON_ORIG = 'data_columns.json'   # copia de columns.json original
OUT_DIR = Path('models')
OUT_DIR.mkdir(exist_ok=True)

# 1) Carga
df = pd.read_excel(DATA_XLS)

# 2) Target + features
target = 'PRECIO_EUR_M2_x'
with open(COLUMNS_JSON_ORIG,'r') as f:
    feature_columns = json.load(f)

# Asegura presencia de columnas
missing = [c for c in feature_columns if c not in df.columns]
if missing:
    raise ValueError(f"Faltan columnas en el Excel: {missing[:5]} ...")

X = df[feature_columns].copy()
y = df[target].astype(float)

# Identifica categóricas de alto cardinal/cadenas
cat_candidates = [c for c in feature_columns if df[c].dtype == 'object']
num_candidates = [c for c in feature_columns if c not in cat_candidates]

preproc = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), cat_candidates),
    ('num', StandardScaler(), num_candidates)
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

def fit_quantile(alpha):
    # GBDT cuantílico scikit-learn
    model = Pipeline([
        ('prep', preproc),
        ('gb', GradientBoostingRegressor(loss='quantile', alpha=alpha, random_state=42, n_estimators=400, max_depth=3))
    ])
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2 = r2_score(y_test, pred)
    print(f"alpha={alpha} | MAE={mae:.2f} | RMSE={rmse:.2f} | R2={r2:.3f}")
    return model

print("Entrenando P10..."); m10 = fit_quantile(0.10)
print("Entrenando P50..."); m50 = fit_quantile(0.50)
print("Entrenando P90..."); m90 = fit_quantile(0.90)

# Guardar artefactos
with open(OUT_DIR/'feature_columns.json','w') as f:
    json.dump(feature_columns, f)

# Extra: separar y guardar preproc por claridad (también está dentro de cada pipeline)
# Para inferencia simple cargaremos los pipelines directamente.
joblib.dump(m10, OUT_DIR/'model_p10.pkl')
joblib.dump(m50, OUT_DIR/'model_p50.pkl')
joblib.dump(m90, OUT_DIR/'model_p90.pkl')
print("✅ Artefactos guardados en models/")

# (Opcional) Guardar explainer SHAP si usas árboles compatibles fuera de Pipeline
try:
    import shap
    explainer = shap.Explainer(m50.named_steps['gb'])
    joblib.dump(explainer, OUT_DIR/'shap_explainer.pkl')
except Exception as e:
    print("SHAP explainer no generado (opcional):", e)
