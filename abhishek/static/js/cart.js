/* static/js/cart.js */
document.addEventListener("DOMContentLoaded", () => {
    const runBtn = document.getElementById("runCartBtn");
    const resultsBox = document.getElementById("resultsBox");
    const loadingState = document.getElementById("loadingState");
    const dpOutput = document.getElementById("dpOutput");
    
    const searchInput = document.getElementById("searchInput");
    const suggestionsBox = document.getElementById("suggestions");
    const cartItemsContainer = document.getElementById("cartItemsContainer");
    const emptyCartMsg = document.getElementById("emptyCartMsg");
    
    const catalogDataRaw = document.getElementById("catalogData").textContent;
    let catalog = { products: [], sellers: [], prices: {} };
    try { catalog = JSON.parse(catalogDataRaw); } catch(e) {}
    
    let cart = []; // Array of product IDs
    
    // --- SEARCH & AUTOCOMPLETE ---
    
    let searchTimeout = null;
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        if (!query) {
            suggestionsBox.style.display = "none";
            return;
        }
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                renderSuggestions(data);
            } catch (err) {
                console.error(err);
            }
        }, 200); // 200ms debounce
    });
    
    function renderSuggestions(products) {
        suggestionsBox.innerHTML = "";
        if (products.length === 0) {
            suggestionsBox.style.display = "none";
            return;
        }
        
        products.forEach(p => {
            const div = document.createElement("div");
            div.style.padding = "0.8rem 1rem";
            div.style.cursor = "pointer";
            div.style.borderBottom = "1px solid var(--border)";
            div.textContent = p.name;
            
            div.addEventListener("mouseover", () => div.style.background = "#F1F5F9");
            div.addEventListener("mouseout", () => div.style.background = "#fff");
            
            div.addEventListener("click", () => {
                addToCart(p.id);
                searchInput.value = "";
                suggestionsBox.style.display = "none";
            });
            
            suggestionsBox.appendChild(div);
        });
        suggestionsBox.style.display = "block";
    }
    
    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = "none";
        }
    });
    
    // --- CART LOGIC ---
    
    function addToCart(pid) {
        if (cart.includes(pid)) {
            alert("This item is already in your cart.");
            return;
        }
        if (cart.length >= 5) {
            alert("Maximum 5 items allowed in cart for this demo.");
            return;
        }
        cart.push(pid);
        renderCart();
    }
    
    window.removeFromCart = function(pid) {
        cart = cart.filter(id => id !== pid);
        renderCart();
    };
    
    async function renderCart() {
        cartItemsContainer.innerHTML = "";
        
        if (cart.length === 0) {
            emptyCartMsg.style.display = "block";
            runBtn.disabled = true;
            return;
        }
        
        emptyCartMsg.style.display = "none";
        runBtn.disabled = false;
        
        for (const pid of cart) {
            let prod = catalog.products.find(p => p.id === pid);
            if (!prod) {
                // Lazily load updated catalog for dynamically generated phones
                try {
                    const res = await fetch("/api/catalog");
                    catalog = await res.json();
                    prod = catalog.products.find(p => p.id === pid);
                } catch (e) {
                    console.error("Failed to load catalog", e);
                }
            }
            if (!prod) continue;
            
            // Find all sellers that sell this
            let availablePrices = [];
            catalog.sellers.forEach(s => {
                const pobj = catalog.prices[s.id]?.[pid];
                if (pobj) {
                    availablePrices.push({
                        seller: s,
                        price: pobj
                    });
                }
            });
            
            // Sort by total cost
            availablePrices.sort((a, b) => a.price.total - b.price.total);
            
            const div = document.createElement("div");
            div.style.border = "1px solid var(--border)";
            div.style.borderRadius = "var(--radius)";
            div.style.padding = "1rem";
            div.style.background = "#fff";
            
            let html = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; font-size: 1.1rem;">${prod.name}</h4>
                    <button onclick="removeFromCart('${pid}')" class="btn btn-outline" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">Remove</button>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.8rem;">
            `;
            
            if (availablePrices.length === 0) {
                html += `<p style="color: var(--danger); font-size: 0.9rem;">Out of stock everywhere</p>`;
            } else {
                availablePrices.forEach((offer, idx) => {
                    const isCheapest = idx === 0;
                    const bg = isCheapest ? "#ECFDF5" : "#F8FAFC";
                    const border = isCheapest ? "1px solid var(--success)" : "1px solid var(--border)";
                    const badge = isCheapest ? `<span class="tag tag-success" style="float: right; font-size: 0.7rem;">Cheapest</span>` : "";
                    
                    let priceHtml = `<div style="font-weight: 600; font-size: 1.1rem; margin-top: 0.5rem;">₹${offer.price.total.toLocaleString()}</div>`;
                    
                    if (offer.price.import_fee > 0) {
                        priceHtml = `
                            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">Base: ₹${offer.price.base.toLocaleString()}</div>
                            <div style="font-size: 0.8rem; color: var(--danger);">Import Fee: +₹${offer.price.import_fee.toLocaleString()}</div>
                            <div style="font-weight: 700; font-size: 1.1rem; margin-top: 0.2rem;">Total: ₹${offer.price.total.toLocaleString()}</div>
                        `;
                    }
                    
                    html += `
                        <div style="background: ${bg}; border: ${border}; border-radius: 6px; padding: 0.8rem;">
                            ${badge}
                            <div style="font-size: 0.85rem; font-weight: 500; color: var(--text-muted);">${offer.seller.name}</div>
                            ${priceHtml}
                        </div>
                    `;
                });
            }
            
            html += `</div>`;
            div.innerHTML = html;
            cartItemsContainer.appendChild(div);
        }
    }
    
    // --- RUN BITMASK DP ---
    
    runBtn.addEventListener("click", async () => {
      runBtn.disabled = true;
      loadingState.style.display = "block";
      resultsBox.style.display = "none";
      
      try {
        const response = await fetch("/api/cart", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            products: cart,
            sellers: catalog.sellers,
            prices: catalog.prices
          })
        });
        const data = await response.json();
        
        loadingState.style.display = "none";
        resultsBox.style.display = "block";
        runBtn.disabled = false;
        
        // Render optimal split
        document.getElementById("totalCost").innerText = `₹${data.best_cost.toLocaleString()}`;
        
        const savingsText = data.comparison.savings_vs_single;
        if (savingsText === null || isNaN(savingsText)) {
            document.getElementById("savingsAmount").innerText = `No single seller stocks everything.`;
        } else {
            document.getElementById("savingsAmount").innerText = `₹${savingsText.toLocaleString()}`;
        }
        
        const planList = document.getElementById("planList");
        planList.innerHTML = "";
        data.plan.forEach(step => {
            const div = document.createElement("div");
            div.style.background = "#fff";
            div.style.border = "1px solid var(--border)";
            div.style.padding = "0.8rem";
            div.style.borderRadius = "6px";
            
            const pnames = step.items.map(pid => {
                const p = catalog.products.find(x => x.id === pid);
                return p ? p.name : pid;
            }).join(", ");
            
            div.innerHTML = `
                <div style="font-weight: 600; margin-bottom: 0.3rem;">Buy from ${step.seller}</div>
                <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">${pnames}</div>
                <div style="font-size: 0.9rem; font-weight: 500;">Cost: ₹${step.cost.toLocaleString()}</div>
            `;
            planList.appendChild(div);
        });
  
        // Run DP Visualiser
        dpOutput.textContent = "Running Bitmask DP...\n\n";
        let i = 0;
        function showStep() {
            if (i >= data.dp_table.length) {
                dpOutput.textContent += `\nDP Complete. Best cost: ₹${data.best_cost.toLocaleString()}`;
                return;
            }
            const s = data.dp_table[i];
            if (s.cost) {
                dpOutput.textContent += `Subset [${s.mask_bin}]: ₹${s.cost.toLocaleString()} (via ${s.from_seller})\n`;
            }
            i++;
            setTimeout(showStep, 50);
        }
        showStep();
  
      } catch (err) {
        alert("Error running Smart Cart: " + err);
        loadingState.style.display = "none";
        runBtn.disabled = false;
      }
    });
    
    // Initial render
    renderCart();
});
