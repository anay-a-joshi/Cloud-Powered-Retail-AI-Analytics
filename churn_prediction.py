# Churn Prediction

# Churn prediction analyzes customer retention by identifying households at risk of disengaging. 
# This process leverages transactional, product, and household data to predict whether a customer 
# will continue to engage or "churn." The analysis starts with data preparation, including cleaning, 
# transforming, and merging datasets. Key features such as the last purchase date are calculated, and 
# a target variable for churn is created, based on customer activity. A Random Forest Classifier is then 
# used to model churn behavior, identifying the most significant factors influencing customer retention. 
# The insights are visualized through a feature importance chart, highlighting the key predictors of churn, 
# and enabling businesses to develop targeted retention strategies. These insights provide valuable guidance 
# for optimizing customer engagement, enhancing loyalty programs, and improving overall business performance.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load datasets
households = pd.read_csv('400_households.csv')
products = pd.read_csv('400_products.csv')
transactions = pd.read_csv('400_transactions.csv')

# Clean column names
households.columns = households.columns.str.strip()
products.columns = products.columns.str.strip()
transactions.columns = transactions.columns.str.strip()

# Merge datasets
data = transactions.merge(products, on="PRODUCT_NUM", how="left")
data = data.merge(households, on="HSHD_NUM", how="left")

# Convert 'PURCHASE_' column to datetime
data['PURCHASE_'] = pd.to_datetime(data['PURCHASE_'], errors='coerce')

# Get the most recent purchase date for each household
data['last_purchase'] = data.groupby('HSHD_NUM')['PURCHASE_'].transform('max')

# Convert 'last_purchase' to datetime if not already
data['last_purchase'] = pd.to_datetime(data['last_purchase'], errors='coerce')

# Create a churn label: customers who have not made a purchase in the last 90 days are considered to have churned
threshold_date = pd.to_datetime('2024-01-01')  # Use the appropriate threshold date here
data['churn'] = (data['last_purchase'] < threshold_date).astype(int)

# Convert datetime columns to numeric (e.g., days since the first purchase)
data['last_purchase_numeric'] = (data['last_purchase'] - data['last_purchase'].min()).dt.days

# Drop non-numeric columns, especially categorical columns like 'STORE_R'
data = data.drop(columns=['HSHD_NUM', 'last_purchase', 'PURCHASE_', 'STORE_R'])

# One-Hot Encode categorical features (if any categorical columns left, such as 'DEPARTMENT', 'COMMODITY')
data = pd.get_dummies(data, drop_first=True)

# Separate features and target variable
X = data.drop(columns=['churn'])
y = data['churn']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Random Forest Model
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
y_pred = rf_model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")

# Classification Report
print(classification_report(y_test, y_pred))

# Feature Importance
importance = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf_model.feature_importances_
}).sort_values(by='Importance', ascending=False)

# Set Neon Colors
neon_colors = {
    'blue': '#00FFFF',
    'pink': '#FF69B4',
    'yellow': '#FFD700',
    'green': '#32CD32'
}

# Plot Feature Importance with Neon Effect
plt.figure(figsize=(8, 5))
plt.barh(importance['Feature'][:5], importance['Importance'][:5], color=neon_colors['blue'], edgecolor=neon_colors['pink'])
plt.xlabel('Importance', fontsize=12, color=neon_colors['yellow'])
plt.ylabel('Feature', fontsize=12, color=neon_colors['yellow'])
plt.title('Top Features for Churn Prediction', fontsize=14, color=neon_colors['green'])
plt.gca().invert_yaxis()

# Add neon color to ticks and grid
plt.xticks(color=neon_colors['yellow'])
plt.yticks(color=neon_colors['yellow'])
plt.grid(color=neon_colors['pink'], linestyle='--', linewidth=0.5, alpha=0.7)

# Adjust layout and save
plt.tight_layout()
plt.savefig('static/feature_importance_churn.png', facecolor='black', bbox_inches="tight")
print("Feature Importance chart saved.")

# Save model accuracy
with open('static/model_accuracy_churn.txt', 'w') as f:
    f.write(f"Model Accuracy: {accuracy:.2f}")
