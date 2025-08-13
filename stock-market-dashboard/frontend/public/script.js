const API_URL = "http://127.0.0.1:8000";

async function loadCompanies() {
    const res = await fetch(`${API_URL}/companies`);
    const companies = await res.json();
    const list = document.getElementById("companyList");
    list.innerHTML = "";
    companies.forEach(c => {
        const div = document.createElement("div");
        div.textContent = `${c.name} (${c.symbol})`;
        div.onclick = () => loadStockData(c.symbol);
        list.appendChild(div);
    });
}

let chart;

async function loadStockData(symbol) {
    const res = await fetch(`${API_URL}/stock/${symbol}`);
    const stock = await res.json();

    if (!stock.data || stock.data.length === 0) {
        alert("No data available for " + symbol);
        return;
    }

    const labels = stock.data.map(d => d.date);
    const prices = stock.data.map(d => d.close);

    if (chart) chart.destroy();

    const ctx = document.getElementById("stockChart").getContext("2d");
    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: `${symbol} Closing Price`,
                data: prices,
                borderColor: "blue",
                fill: false
            }]
        }
    });

    // Show stats
    const statsDiv = document.getElementById("stockStats");
    statsDiv.innerHTML = `
        <p><strong>52-Week High:</strong> ${stock.high_52w}</p>
        <p><strong>52-Week Low:</strong> ${stock.low_52w}</p>
        <p><strong>Average Volume:</strong> ${stock.avg_volume.toLocaleString()}</p>
        <p><strong>Predicted Next Close:</strong> ${stock.predicted_price}</p>
    `;
}

loadCompanies();



