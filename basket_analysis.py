# Basket Analysis

# Basket analysis is a comprehensive approach to understanding customer purchasing behaviors by examining 
# transactional, product, and household data. This analysis identifies patterns and associations, highlighting 
# commonly purchased product combinations to uncover cross-selling opportunities and customer preferences. 
# The workflow begins with data preparation, merging transactional, product, and household datasets to create 
# a unified view. Using one-hot encoding, product purchases are transformed into a format suitable for machine 
# learning models. A Random Forest Classifier is then applied to predict product associations and identify key 
# features influencing purchase behavior. The insights are visualized through a feature importance chart, showcasing 
# top products frequently purchased with the target item, a network graph illustrating associations between products, 
# and a co-purchase heatmap highlighting the frequency of product combinations. These visualizations provide actionable 
# insights for strategic decisions, such as inventory optimization, personalized marketing, and enhancing the overall 
# customer shopping experience.

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load datasets
households = pd.read_csv('400_households.csv')
products = pd.read_csv('400_products.csv')
transactions = pd.read_csv('400_transactions.csv')

# Set global style for neon effect
plt.style.use('dark_background')

# Neon colors for graphs
neon_colors = {
    'blue': '#00FFFF',
    'pink': '#FF69B4',
    'yellow': '#FFD700',
    'green': '#32CD32'
}

# Clean column names
households.columns = households.columns.str.strip()
products.columns = products.columns.str.strip()
transactions.columns = transactions.columns.str.strip()

# Merge datasets
data = transactions.merge(products, on="PRODUCT_NUM", how="left")
data = data.merge(households, on="HSHD_NUM", how="left")

# Basket Analysis Preparation
basket_data = data.groupby(['BASKET_NUM', 'HSHD_NUM'])['COMMODITY'].apply(list).reset_index()

# One-hot encoding
from mlxtend.preprocessing import TransactionEncoder
te = TransactionEncoder()
basket_matrix = te.fit_transform(basket_data['COMMODITY'])
basket_df = pd.DataFrame(basket_matrix, columns=te.columns_)
basket_df['HSHD_NUM'] = basket_data['HSHD_NUM']
basket_df['BASKET_NUM'] = basket_data['BASKET_NUM']

# Define target product
target_product = 'DAIRY'

# Check if target product is in columns, and dynamically choose another if not
if target_product not in basket_df.columns:
    print(f"Target product '{target_product}' not found.")
    # Dynamically select another product from the columns
    available_products = [col for col in basket_df.columns if col not in ['HSHD_NUM', 'BASKET_NUM']]
    if available_products:
        target_product = available_products[0]  # Choose the first available product
        print(f"Using '{target_product}' as the new target product.")
    else:
        raise ValueError("No valid products available for analysis!")

# Proceed with feature-target split
X = basket_df.drop(columns=[target_product, 'HSHD_NUM', 'BASKET_NUM'])
y = basket_df[target_product]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Random Forest Model
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
y_pred = rf_model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy:.2f}")

# Save accuracy to a text file
with open('static/model_accuracy.txt', 'w') as f:
    f.write(f"Model Accuracy: {accuracy:.2f}")

# Feature importance
importance = pd.DataFrame({
    'Product': X.columns,
    'Importance': rf_model.feature_importances_
}).sort_values(by='Importance', ascending=False)

# Save Feature Importance Bar Chart
plt.figure(figsize=(8, 5))
plt.barh(importance['Product'][:5], importance['Importance'][:5], color=neon_colors['blue'], edgecolor=neon_colors['pink'])
plt.xlabel('Importance', fontsize=12, color=neon_colors['yellow'])
plt.ylabel('Product', fontsize=12, color=neon_colors['yellow'])
plt.title(f'Top Products Frequently Purchased with {target_product}', fontsize=14, color=neon_colors['green'])
plt.gca().invert_yaxis()
plt.xticks(color=neon_colors['yellow'])
plt.yticks(color=neon_colors['yellow'])
plt.grid(color=neon_colors['pink'], linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()  # Adjust layout
plt.savefig('static/feature_importance.png', facecolor='black', bbox_inches="tight")
print("Feature Importance Bar Chart saved.")

# Create Network Graph
co_occurrence = basket_df.drop(columns=['HSHD_NUM', 'BASKET_NUM']).T.dot(
    basket_df.drop(columns=['HSHD_NUM', 'BASKET_NUM'])
)
np.fill_diagonal(co_occurrence.values, 0)

G = nx.Graph()
threshold = 0.05
for product_a, product_b in co_occurrence.stack().index:
    weight = co_occurrence.loc[product_a, product_b]
    if weight > threshold:
        G.add_edge(product_a, product_b, weight=weight)

# Save Network Graph
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G, k=0.3, seed=42)
nx.draw_networkx_nodes(G, pos, node_size=700, node_color=neon_colors['green'])
nx.draw_networkx_edges(G, pos, edgelist=G.edges(data=True), width=1.0, alpha=0.7, edge_color=neon_colors['blue'])
nx.draw_networkx_labels(G, pos, font_size=10, font_color=neon_colors['yellow'], font_weight="bold")
plt.title("Network Graph of Product Associations", fontsize=14, color=neon_colors['pink'])
plt.tight_layout()  # Adjust layout
plt.savefig('static/product_network.png', facecolor='black', bbox_inches="tight")
print("Network Graph saved.")

# Save Heatmap
plt.figure(figsize=(12, 10))
ax = sns.heatmap(co_occurrence, cmap='cool', linewidths=0.5, annot=False, square=True,
                 linecolor=neon_colors['pink'])
# Style the color bar
cbar = ax.collections[0].colorbar
cbar.ax.yaxis.set_tick_params(color=neon_colors['yellow'])
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=neon_colors['yellow'])
# Add title
plt.title('Co-Purchase Frequency Heatmap', fontsize=14, color=neon_colors['yellow'])
plt.tight_layout()  # Adjust layout
plt.savefig('static/heatmap.png', facecolor='black', bbox_inches="tight")
print("Heatmap with neon effect saved.")