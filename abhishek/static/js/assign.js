/* static/js/assign.js */
document.addEventListener("DOMContentLoaded", () => {
    const runBtn = document.getElementById("runAssignBtn");
    const resultsBox = document.getElementById("resultsBox");
    const loadingState = document.getElementById("loadingState");
    const flowOutput = document.getElementById("flowOutput");
    
    // UI Elements for interactivity
    const buyerInput = document.getElementById("buyerInput");
    const productInput = document.getElementById("productInput");
    const qtyInput = document.getElementById("qtyInput");
    const addOrderBtn = document.getElementById("addOrderBtn");
    const productSuggestions = document.getElementById("productSuggestions");
    
    const ordersTableBody = document.getElementById("ordersTableBody");
    const sellersTableBody = document.getElementById("sellersTableBody");
    
    const assignDataRaw = document.getElementById("assignData").textContent;
    let state = { orders: [], sellers: [] };
    try { state = JSON.parse(assignDataRaw); } catch(e) {}
    
    let orderCounter = state.orders.length;

    // --- INITIAL RENDER ---
    function renderTables() {
        // Render Orders
        ordersTableBody.innerHTML = "";
        state.orders.forEach((o, index) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${o.buyer}</td>
                <td>${o.product}</td>
                <td style="font-weight: 600;">${o.qty}</td>
                <td><button onclick="removeOrder(${index})" class="btn btn-outline" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">Remove</button></td>
            `;
            ordersTableBody.appendChild(tr);
        });

        // Render Sellers
        sellersTableBody.innerHTML = "";
        state.sellers.forEach(s => {
            const tr = document.createElement("tr");
            
            let stocksHtml = "";
            for (const [prod, stock] of Object.entries(s.stocks)) {
                if (stock > 0) {
                    stocksHtml += `<div>${prod}: <span style="font-weight:600">${stock}</span></div>`;
                }
            }
            if (!stocksHtml) stocksHtml = `<span style="color:var(--text-muted)">Out of stock</span>`;
            
            tr.innerHTML = `
                <td style="font-weight: 500;">${s.name}</td>
                <td>${s.capacity} items max</td>
                <td style="font-size: 0.85rem; color: var(--text-muted);">${stocksHtml}</td>
            `;
            sellersTableBody.appendChild(tr);
        });
    }

    window.removeOrder = function(index) {
        state.orders.splice(index, 1);
        renderTables();
    };

    renderTables();

    // --- PRODUCT SEARCH (AUTOCOMPLETE) ---
    let searchTimeout = null;
    productInput.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        if (!query) {
            productSuggestions.style.display = "none";
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
        }, 200);
    });

    function renderSuggestions(products) {
        productSuggestions.innerHTML = "";
        if (products.length === 0) {
            productSuggestions.style.display = "none";
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
                productInput.value = p.name; // Keep the full name, not the ID
                productSuggestions.style.display = "none";
            });
            
            productSuggestions.appendChild(div);
        });
        productSuggestions.style.display = "block";
    }

    document.addEventListener("click", (e) => {
        if (!productInput.contains(e.target) && !productSuggestions.contains(e.target)) {
            productSuggestions.style.display = "none";
        }
    });

    // --- ADD CUSTOM ORDER ---
    addOrderBtn.addEventListener("click", () => {
        const buyer = buyerInput.value.trim();
        const product = productInput.value.trim();
        const qty = parseInt(qtyInput.value, 10);

        if (!buyer || !product || isNaN(qty) || qty <= 0) {
            alert("Please fill all fields correctly.");
            return;
        }

        orderCounter++;
        state.orders.push({
            id: `o${orderCounter}`,
            product: product,
            qty: qty,
            buyer: buyer
        });

        // To make the demo work, dynamically inject stock of this product into random sellers
        let totalInjectedStock = 0;
        const targetStock = qty + Math.floor(Math.random() * 5); // Add just enough stock
        
        state.sellers.forEach(s => {
            // Randomly give stock to sellers
            if (Math.random() > 0.2 && totalInjectedStock < targetStock) {
                const stockToGive = Math.min(
                    targetStock - totalInjectedStock, 
                    Math.floor(Math.random() * qty) + 3
                );
                
                if (stockToGive > 0) {
                    s.stocks[product] = (s.stocks[product] || 0) + stockToGive;
                    // Dynamically increase their shipping capacity so this new stock can actually flow!
                    s.capacity += stockToGive;
                    totalInjectedStock += stockToGive;
                }
            }
        });
        
        // Failsafe: if random rolls failed to inject enough, dump the rest into the first seller
        if (totalInjectedStock < qty) {
            const remainder = qty - totalInjectedStock;
            state.sellers[0].stocks[product] = (state.sellers[0].stocks[product] || 0) + remainder;
            state.sellers[0].capacity += remainder;
        }

        buyerInput.value = "";
        productInput.value = "";
        qtyInput.value = "";
        renderTables();
    });

    // --- RUN ASSIGNMENT (MAX FLOW) ---
    runBtn.addEventListener("click", async () => {
      if (state.orders.length === 0) {
          alert("Please add at least one customer order.");
          return;
      }

      runBtn.disabled = true;
      loadingState.style.display = "block";
      resultsBox.style.display = "none";
      
      try {
        const response = await fetch("/api/assign", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            orders: state.orders,
            sellers: state.sellers
          })
        });
        const data = await response.json();
        
        loadingState.style.display = "none";
        resultsBox.style.display = "block";
        runBtn.disabled = false;
        
        // Render optimal assignment
        document.getElementById("totalFulfilled").innerText = `${data.max_flow} / ${data.total_demand}`;
        if (data.max_flow === data.total_demand) {
            document.getElementById("totalFulfilled").style.color = "var(--success)";
        } else {
            document.getElementById("totalFulfilled").style.color = "var(--accent)";
        }
        
        const tbody = document.getElementById("planTableBody");
        tbody.innerHTML = "";
        data.assignment.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight: 500;">${row.seller}</td>
                <td>${row.order}</td>
                <td style="font-weight: 700; color: var(--accent);">${row.qty}</td>
            `;
            tbody.appendChild(tr);
        });
  
        // Run Flow Visualiser
        flowOutput.textContent = "Running Edmonds-Karp BFS...\n\n";
        let i = 0;
        function showStep() {
            if (i >= data.steps.length) {
                flowOutput.textContent += `\nMax Flow Reached. Total Fulfilled: ${data.max_flow}`;
                return;
            }
            const s = data.steps[i];
            
            // Format path
            let pathStr = "";
            for (let j = 0; j < s.path.length; j++) {
                let node = s.path[j].replace(/\n/g, " ");
                pathStr += node;
                if (j < s.path.length - 1) pathStr += " → ";
            }
            
            flowOutput.textContent += `Path ${i+1}: ${pathStr}\n`;
            flowOutput.textContent += `Bottleneck: +${s.bottleneck} units (Total flow so far: ${s.total_flow})\n\n`;
            i++;
            setTimeout(showStep, 200);
        }
        showStep();
  
      } catch (err) {
        alert("Error running Assignment: " + err);
        loadingState.style.display = "none";
        runBtn.disabled = false;
      }
    });
});
