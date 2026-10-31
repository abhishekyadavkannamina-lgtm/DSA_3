# 🛍️ Product Match Lab

Welcome to **Product Match Lab**! Have you ever searched for a phone online and found 50 different listings with slightly different names ("Samsung S24", "Galaxy S24 5G", "S24 Black") and completely different prices? 

It's confusing, messy, and makes finding the best deal impossible. **We fix that.**

Product Match Lab is an intelligent e-commerce platform that takes messy product listings from all over the internet, figures out which ones are actually the exact same item, and groups them together. Then, we give you advanced tools to guarantee you're getting the absolute cheapest price possible.

---

## ✨ Features

### 1. 🔍 Match Listings (The Catalog Cleaner)
We crawl thousands of real-world messy listings from sources like Amazon, BestBuy, and Flipkart. Our system automatically detects identical products and groups them into clean, single product pages. No more scrolling through duplicates!

### 2. 🛒 Smart Cart (The Money Saver)
When you add items to your cart, prices can vary wildly between sellers, and shipping costs complicate things further. Click the **"Find Cheapest Cart"** button, and our system will calculate billions of possible combinations to find the absolute cheapest way to buy everything you want—even if it means buying from 3 different sellers!

### 3. 📦 Order Assignment (The Logistics Master)
When a business receives hundreds of bulk orders but has limited stock scattered across different warehouses, deciding who gets what is a nightmare. Our Order Assignment system automatically routes inventory to fulfill the maximum number of orders instantly.

---

## 🎨 The Design
This project doesn't just work well; it looks incredible. It features a fully custom **Premium iOS Frosted Glassmorphism** user interface. 
- Vibrant, slow-moving liquid background blobs
- Highly translucent frosted glass components
- Floating glass navigation

*Everything is built from scratch using pure Vanilla CSS, HTML, and Python—no bloated frameworks!*

---

## 🚀 How to Run the App

Running the project on your computer is super simple. Just open your terminal and follow these steps:

**1. Create a virtual environment (optional but recommended):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**2. Install the required tools:**
```bash
pip install -r requirements.txt
```

**3. Start the server!**
```bash
python app.py
```

**4. Open the App:**
Open your web browser and go to: **http://127.0.0.1:5000**

*(If you want to update the catalog with new phones from the real-world dataset, simply run `python data/build_dataset.py` before starting the server).*

---

## 🧠 What's under the hood?
For the tech-savvy, this beautiful UI is powered by hardcore computer science algorithms built entirely from scratch:
- **Rabin-Karp Rolling Hash:** Used to instantly compare and match text in the Smart Cart search.
- **Disjoint Sets (Union-Find):** Used to magically group similar product listings together.
- **Bitmask Dynamic Programming:** The mathematical brain that calculates the cheapest cart combinations.
- **Edmonds-Karp (Max Flow):** The logistics algorithm that routes inventory through a network graph to fulfill bulk orders.

Built with ❤️ by Team 9.
