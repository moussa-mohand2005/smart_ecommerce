import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import xgboost as xgb
import pymysql
import warnings
import os
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "smart_ecommerce"),
        charset="utf8mb4"
    )

def calculate_scores(df):
    df['rating_avg'] = pd.to_numeric(df['rating_avg'], errors='coerce').fillna(0)
    df['reviews_count'] = pd.to_numeric(df['reviews_count'], errors='coerce').fillna(0)
    df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce')
    median_price = df['current_price'].median()
    df['current_price'] = df['current_price'].fillna(median_price if pd.notnull(median_price) else 0)
    df['in_stock'] = df['stock_status'].apply(lambda x: 1 if x and 'instock' in str(x).lower() else 0)

    scaler = MinMaxScaler()
    df['score_price'] = 1 - scaler.fit_transform(df[['current_price']]).flatten() if df['current_price'].nunique() > 1 else 1.0
    df['score_rating'] = scaler.fit_transform(df[['rating_avg']]).flatten() if df['rating_avg'].nunique() > 1 else 1.0
    df['score_reviews'] = scaler.fit_transform(df[['reviews_count']]).flatten() if df['reviews_count'].nunique() > 1 else 1.0

    df['ml_score'] = (df['score_rating'] * 0.4 + df['score_reviews'] * 0.3 + df['score_price'] * 0.2 + df['in_stock'] * 0.1) * 100
    return df

def run_clustering(df):
    df['all_notes'] = (df['material'].fillna('') + " " + df['sole_type'].fillna('') + " " + df['closure'].fillna('')).str.strip()
    if df['all_notes'].str.len().sum() > 0:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        X = vectorizer.fit_transform(df['all_notes'])
        n_clusters = min(5, X.shape[0])
        if n_clusters > 1:
            
            if np.unique(X.toarray(), axis=0).shape[0] < n_clusters:
                n_clusters = max(1, np.unique(X.toarray(), axis=0).shape[0])
            
            if n_clusters > 1:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
                labels = kmeans.fit_predict(X)
                df['cluster_id'] = labels
                try:
                    score = silhouette_score(X, labels)
                    print(f"Silhouette Score: {score:.3f}")
                except: pass
            else: df['cluster_id'] = 0
        else: df['cluster_id'] = 0
    else: df['cluster_id'] = 0
    return df

def run_pca(df):
    """Réduit les dimensions pour la visualisation dans le dashboard (Footwear)."""
    df['all_features'] = (df['material'].fillna('') + " " + df['sole_type'].fillna('') + " " + df['closure'].fillna('')).str.strip()
    if df['all_features'].str.len().sum() > 0:
        vectorizer = TfidfVectorizer(max_features=50)
        X = vectorizer.fit_transform(df['all_features']).toarray()
        pca = PCA(n_components=2)
        coords = pca.fit_transform(X)
        df['pca_x'] = coords[:, 0]
        df['pca_y'] = coords[:, 1]
    return df

def run_predictive_model(df):
    """Entraîne un modèle XGBoost pour prédire le 'Succès Potentiel' avec évaluation."""
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    
    # Simulation de 'target' si non présente
    df['target_success'] = df['ml_score'] * (1 + 0.1 * (df['reviews_count'] > df['reviews_count'].median()))
    
    features = ['score_price', 'score_rating', 'score_reviews', 'in_stock']
    X = df[features]
    y = df['target_success']
    
    # Split for evaluation as required by the project specs
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\n--- Model Evaluation (Supervised Learning - XGBoost) ---")
    model = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"R² Score: {r2:.4f}")
    
    # Simple binary evaluation (Success > 60) for metrics like Precision/Recall if translated to class
    y_test_class = (y_test > 60).astype(int)
    y_pred_class = (y_pred > 60).astype(int)
    from sklearn.metrics import classification_report
    print("\nClassification Report (Success Threshold > 60):")
    print(classification_report(y_test_class, y_pred_class, labels=[0, 1], target_names=['Normal', 'Top']))

    # Predict for all rows for the dashboard
    df['predicted_success'] = model.predict(X)
    return df


def run_association_rules(df):
    from mlxtend.frequent_patterns import apriori, association_rules
    transactions = []
    for _, row in df.iterrows():
        notes = []
        for col in ['material', 'sole_type', 'closure']:
            if pd.notna(row[col]): notes.extend([n.strip().lower() for n in str(row[col]).split(',') if n.strip()])
        if notes: transactions.append(list(set(notes)))
    if not transactions: return pd.DataFrame()
    mlb = MultiLabelBinarizer()
    df_binary = pd.DataFrame(mlb.fit_transform(transactions), columns=mlb.classes_).astype(bool)
    frequent_itemsets = apriori(df_binary, min_support=0.04, use_colnames=True)
    if frequent_itemsets.empty: return pd.DataFrame()
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.1)
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    return rules.sort_values('lift', ascending=False)

def main():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM products WHERE is_enriched=TRUE", conn)
        df['product_id'] = pd.to_numeric(df['product_id'], errors='coerce')
        df = df.dropna(subset=['product_id'])
        if df.empty: return
        
        print(f"Analyzing {len(df)} products...")
        df = calculate_scores(df)
        df = run_clustering(df)
        df = run_pca(df)
        df = run_predictive_model(df)
        
        rules = run_association_rules(df)
        if not rules.empty: rules.to_csv("footwear_correlations.csv", index=False)

        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute("""
                    UPDATE products SET 
                        ml_score=%s, cluster_id=%s, 
                        pca_x=%s, pca_y=%s, predicted_success=%s 
                    WHERE product_id=%s
                """, (
                    float(row['ml_score']), int(row['cluster_id']), 
                    float(row.get('pca_x', 0)), float(row.get('pca_y', 0)),
                    float(row.get('predicted_success', 0)),
                    int(row['product_id'])
                ))
        conn.commit()
        print("ML Analysis Success.")
    except Exception as e: print(f"Error: {e}")
    finally: conn.close()

if __name__ == "__main__":
    main()
