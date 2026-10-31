import pandas as pd
import json
import pathlib

ROOT = pathlib.Path(__file__).parent

def update_catalog():
    listings_path = ROOT / "listings.csv"
    if not listings_path.exists():
        print("listings.csv not found")
        return
        
    df = pd.read_csv(listings_path)
    # Filter for matched products
    matched = df[df["true_product_id"] != "UNMATCHED"].copy()
    
    products = []
    prices_dict = {}
    
    # We will build a list of unique sellers dynamically
    sellers_dict = {}
    
    # Define import fee logic (e.g., US/UK/DE sellers have 28% import fee)
    def get_import_fee(seller_name, price):
        seller_lower = str(seller_name).lower()
        if "us" in seller_lower or "uk" in seller_lower or "de" in seller_lower:
            return round(price * 0.28)
        return 0

    # Define shipping logic
    def get_shipping(seller_name):
        seller_lower = str(seller_name).lower()
        if "amazon" in seller_lower: return 0
        if "flipkart" in seller_lower: return 50
        if "best buy" in seller_lower: return 150
        return 99

    for pid, group in matched.groupby("true_product_id"):
        # The canonical name is the longest cleaned title (or just the most common title)
        name = group["title"].value_counts().idxmax()
        # Clean it up a bit for display
        name = name.title()
        
        products.append({"id": pid, "name": name})
        
        for _, row in group.iterrows():
            seller = row["seller"]
            if pd.isna(seller): continue
                
            sid = seller.replace(" ", "_").lower()
            if sid not in sellers_dict:
                sellers_dict[sid] = {
                    "id": sid, 
                    "name": seller, 
                    "shipping": get_shipping(seller),
                    "is_foreign": "amazon" in seller.lower() and not "india" in seller.lower() and ("us" in seller.lower() or "uk" in seller.lower() or "de" in seller.lower())
                }
            
            if sid not in prices_dict:
                prices_dict[sid] = {}
                
            base_price = int(row["price_inr"])
            import_fee = get_import_fee(seller, base_price)
            
            # Store price object for UI
            # Bitmask DP expects a flat float cost, so we will store total_cost for DP, but pass an object for UI
            # Wait, our existing solve_bitmask_dp expects prices to be a float. 
            # I'll just change the DP script to accept a dict, or I can pass total cost directly.
            # Let's pass the total cost to DP, but in the JSON we store the rich object.
            prices_dict[sid][pid] = {
                "base": base_price,
                "import_fee": import_fee,
                "total": base_price + import_fee
            }

    catalog_data = {
        "products": products,
        "sellers": list(sellers_dict.values()),
        "prices": prices_dict
    }
    
    with open(ROOT / "catalog_data.json", "w") as f:
        json.dump(catalog_data, f, indent=2)
    
    print(f"✅ Generated catalog_data.json with {len(products)} products and {len(sellers_dict)} sellers.")

if __name__ == "__main__":
    update_catalog()
