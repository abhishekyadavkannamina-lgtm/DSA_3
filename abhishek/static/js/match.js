/* static/js/match.js */
document.addEventListener("DOMContentLoaded", () => {
    const runBtn = document.getElementById("runPipelineBtn");
    const rawSection = document.getElementById("rawSection");
    const loadingState = document.getElementById("loadingState");
    const resultsSection = document.getElementById("resultsSection");
    const groupsContainer = document.getElementById("groupsContainer");
    
    // Parse listings from the script tag
    const listingsRaw = document.getElementById("listingsData").textContent;
    let listings = [];
    try { listings = JSON.parse(listingsRaw); } catch(e) {}
  
    runBtn.addEventListener("click", async () => {
      runBtn.disabled = true;
      rawSection.style.display = "none";
      loadingState.style.display = "block";
  
      try {
        const response = await fetch("/api/match", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ listings: listings, threshold: 0.80 })
        });
        const data = await response.json();
        
        loadingState.style.display = "none";
        resultsSection.style.display = "block";
        
        renderGroups(data.groups);
        
        if (data.evaluation) {
          document.getElementById("evalPrecision").innerText = data.evaluation.precision;
          document.getElementById("evalRecall").innerText = data.evaluation.recall;
          document.getElementById("evalF1").innerText = data.evaluation.f1;
        }
  
      } catch (err) {
        alert("Error running pipeline: " + err);
        loadingState.style.display = "none";
        rawSection.style.display = "block";
        runBtn.disabled = false;
      }
    });
  
    function renderGroups(groups) {
      groupsContainer.innerHTML = "";
      for (const [gid, gdata] of Object.entries(groups)) {
        const div = document.createElement("div");
        div.className = "card";
        div.style.background = "#fff";
        div.style.border = "1px solid var(--border)";
        
        const count = gdata.listings.length;
        let sourcesHtml = gdata.listings.map(l => `<span class="tag">${l.seller}</span>`).join(" ");
        
        div.innerHTML = `
          <h4 style="margin-top:0; margin-bottom: 0.5rem; font-size: 1.05rem;">${gdata.canonical}</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">Merged ${count} listings</p>
          <div style="margin-bottom: 1rem;">${sourcesHtml}</div>
          <div style="background: #F8FAFC; padding: 0.8rem; border-radius: 6px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.9rem; font-weight: 500;">Best from ${gdata.best_seller}</span>
            <span style="color: var(--success); font-weight: 700; font-size: 1.1rem;">₹${gdata.best_price.toLocaleString()}</span>
          </div>
        `;
        groupsContainer.appendChild(div);
      }
    }
  
    // Visualiser
    const vizRunBtn = document.getElementById("vizRunBtn");
    vizRunBtn.addEventListener("click", async () => {
      const text = document.getElementById("vizText").value;
      const pattern = document.getElementById("vizPattern").value;
      const out = document.getElementById("vizOutput");
      out.textContent = "Calculating hashes...\n";
  
      const res = await fetch("/api/rabin-karp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, pattern })
      });
      const data = await res.json();
      
      if (data.steps.length === 0) {
        out.textContent += "Pattern too long or empty.";
        return;
      }
      
      out.textContent += `Pattern Hash: ${data.steps[0].pat_hash}\n\n`;
      let i = 0;
      function showStep() {
        if (i >= data.steps.length) {
          out.textContent += `\nDone. Found at positions: [${data.positions.join(", ")}]`;
          return;
        }
        const s = data.steps[i];
        let mark = s.result === "match" ? "✅ MATCH" : (s.result === "collision" ? "⚠️ COLLISION" : "❌");
        out.textContent += `Window: "${s.window}" | Hash: ${s.win_hash} -> ${mark}\n`;
        i++;
        setTimeout(showStep, 100);
      }
      showStep();
    });
  });
