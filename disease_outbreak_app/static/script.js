document.addEventListener('DOMContentLoaded', () => {

    // --- 1. DOM Element References ---
    const loader = document.getElementById('loader');
    const dashboardContent = document.getElementById('dashboard-content');
    const themeToggleButton = document.getElementById('theme-toggle');
    
    // Chart Canvases
    const pieChartCanvas = document.getElementById('pieChart').getContext('2d');
    const barChartCanvas = document.getElementById('barChart').getContext('2d');
    const forecastVsHistoryCanvas = document.getElementById('forecastVsHistoryChart').getContext('2d');
    const regionalRiskCanvas = document.getElementById('regionalRiskChart').getContext('2d');
    
    // Table and Controls
    const dataTableContainer = document.getElementById('dataTableContainer');
    const searchInput = document.getElementById('searchInput');
    const riskFilter = document.getElementById('riskFilter');
    
    // Header Stats
    const totalCountriesEl = document.getElementById('totalCountries');
    const highRiskCountEl = document.getElementById('highRiskCount');

    const API_URL = '/disease-outbreak/api/global-forecast';
    
    // Chart instances and data storage
    let pieChart, barChart, forecastVsHistoryChart, regionalRiskChart;
    let fullData = []; // Store full data for filtering

    // --- 2. Enhanced Dark Mode Logic ---
    function applyTheme(theme) {
        document.body.classList.toggle('dark-mode', theme === 'dark');
        
        // Animate the toggle slider
        const slider = document.querySelector('.toggle-slider');
        if (theme === 'dark') {
            slider.style.transform = 'translateX(34px)';
        } else {
            slider.style.transform = 'translateX(0)';
        }
    }

    themeToggleButton.addEventListener('click', () => {
        const newTheme = document.body.classList.contains('dark-mode') ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
        updateChartTheme(newTheme);
    });

    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // --- 3. Enhanced Data Fetching and Processing ---
    async function fetchDataAndRenderCharts() {
        try {
            // Add loading animation delay for better UX
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const response = await fetch(API_URL);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            // Store full data for filtering
            fullData = data;

            // Update header stats
            updateHeaderStats(data);

            // Process data for each visualization
            const riskCounts = processForPieChart(data);
            const highRiskCountries = processForBarChart(data);
            const regionalData = processForRegionalChart(data);

            // Hide loader and show content with animation
            loader.style.display = 'none';
            dashboardContent.classList.remove('hidden');
            
            // Add entrance animation
            setTimeout(() => {
                dashboardContent.style.opacity = '1';
                dashboardContent.style.transform = 'translateY(0)';
            }, 100);

            // Render all visualizations
            renderPieChart(riskCounts);
            renderBarChart(highRiskCountries);
            renderForecastVsHistoryChart(highRiskCountries);
            renderRegionalRiskChart(regionalData);
            renderDataTable(data);

            // Apply theme to all charts
            updateChartTheme(localStorage.getItem('theme') || 'light');

        } catch (error) {
            console.error("Failed to fetch or process data:", error);
            loader.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Failed to load data</h3>
                    <p>Please check your connection and try again.</p>
                    <button onclick="location.reload()" class="retry-btn">Retry</button>
                </div>
            `;
        }
    }

    // --- 4. Update Header Statistics ---
    function updateHeaderStats(data) {
        const totalCountries = data.length;
        const highRiskCount = data.filter(d => d.Risk_Level === 'High').length;
        
        // Animate counter
        animateCounter(totalCountriesEl, 0, totalCountries, 1500);
        animateCounter(highRiskCountEl, 0, highRiskCount, 1500);
    }

    function animateCounter(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    }

    // --- 5. Enhanced Data Processing Functions ---
    function processForPieChart(data) {
        return data.reduce((acc, item) => {
            acc[item.Risk_Level] = (acc[item.Risk_Level] || 0) + 1;
            return acc;
        }, {});
    }

    function processForBarChart(data) {
        return data
            .filter(d => d.Risk_Level === 'High')
            .sort((a, b) => b.Forecasted_Cases - a.Forecasted_Cases)
            .slice(0, 15);
    }

    function processForRegionalChart(data) {
        const countryToRegion = { 
            USA: 'Americas', IND: 'Asia', NGA: 'Africa', BRA: 'Americas', 
            PAK: 'Asia', IDN: 'Asia', SEAR: 'Asia', WB_LI: 'Other', 
            NER: 'Africa', TCD: 'Africa', WPR: 'Asia', SOM: 'Africa', 
            WB_UMI: 'Other', KEN: 'Africa', AFG: 'Asia', SSD: 'Africa', 
            LAO: 'Asia', PHL: 'Asia'
        };
        
        const regions = { 
            Americas: { High: 0, Medium: 0, Low: 0 }, 
            Asia: { High: 0, Medium: 0, Low: 0 }, 
            Africa: { High: 0, Medium: 0, Low: 0 }, 
            Other: { High: 0, Medium: 0, Low: 0 } 
        };
        
        data.forEach(country => {
            const region = countryToRegion[country.CountryCode] || 'Other';
            regions[region][country.Risk_Level]++;
        });
        
        return regions;
    }

    // --- 6. Enhanced Chart Rendering Functions ---
    function renderPieChart(riskData) {
        const colors = {
            'High': 'linear-gradient(135deg, #ef4444, #dc2626)',
            'Medium': 'linear-gradient(135deg, #f59e0b, #d97706)',
            'Low': 'linear-gradient(135deg, #10b981, #059669)'
        };

        pieChart = new Chart(pieChartCanvas, {
            type: 'doughnut',
            data: {
                labels: Object.keys(riskData),
                datasets: [{
                    data: Object.values(riskData),
                    backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                    borderWidth: 0,
                    hoverBorderWidth: 4,
                    hoverBorderColor: 'rgba(255, 255, 255, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12, weight: '500' }
                        }
                    }
                },
                cutout: '60%',
                animation: {
                    animateRotate: true,
                    duration: 2000
                }
            }
        });
    }

    function renderBarChart(countryData) {
        barChart = new Chart(barChartCanvas, {
            type: 'bar',
            data: {
                labels: countryData.map(c => c.CountryCode),
                datasets: [{
                    label: 'Forecasted Cases',
                    data: countryData.map(c => c.Forecasted_Cases),
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    borderRadius: 6,
                    hoverBackgroundColor: '#ef4444',
                    hoverBorderColor: '#dc2626'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    function renderForecastVsHistoryChart(countryData) {
        forecastVsHistoryChart = new Chart(forecastVsHistoryCanvas, {
            type: 'bar',
            data: {
                labels: countryData.map(c => c.CountryCode),
                datasets: [
                    {
                        label: 'Forecasted Cases',
                        data: countryData.map(c => c.Forecasted_Cases),
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        borderRadius: 6
                    },
                    {
                        label: '10-Year Average Cases',
                        data: countryData.map(c => c.Mean_Cases_10Y),
                        backgroundColor: 'rgba(107, 114, 128, 0.8)',
                        borderColor: '#6b7280',
                        borderWidth: 2,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12, weight: '500' }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    function renderRegionalRiskChart(regionalData) {
        regionalRiskChart = new Chart(regionalRiskCanvas, {
            type: 'bar',
            data: {
                labels: Object.keys(regionalData),
                datasets: [
                    {
                        label: 'High Risk',
                        data: Object.values(regionalData).map(r => r.High),
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        borderRadius: 6
                    },
                    {
                        label: 'Medium Risk',
                        data: Object.values(regionalData).map(r => r.Medium),
                        backgroundColor: 'rgba(245, 158, 11, 0.8)',
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        borderRadius: 6
                    },
                    {
                        label: 'Low Risk',
                        data: Object.values(regionalData).map(r => r.Low),
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: '#10b981',
                        borderWidth: 2,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12, weight: '500' }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        beginAtZero: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // --- 7. Enhanced Data Table with Search and Filter ---
    function renderDataTable(data) {
        const tableHTML = generateTableHTML(data);
        dataTableContainer.innerHTML = tableHTML;
    }

    function generateTableHTML(data) {
        let tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Country</th>
                        <th>Risk Level</th>
                        <th>Forecasted Cases</th>
                        <th>10Y Avg. Cases</th>
                        <th>Difference</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        data.sort((a, b) => b.Forecasted_Cases - a.Forecasted_Cases).forEach(country => {
            const difference = country.Forecasted_Cases - country.Mean_Cases_10Y;
            const differenceClass = difference > 0 ? 'increase' : 'decrease';
            const differenceIcon = difference > 0 ? '▲' : '▼';
            
            tableHTML += `
                <tr>
                    <td><strong>${country.CountryCode}</strong></td>
                    <td><span class="risk-badge risk-${country.Risk_Level.toLowerCase()}">${country.Risk_Level}</span></td>
                    <td>${Math.round(country.Forecasted_Cases).toLocaleString()}</td>
                    <td>${Math.round(country.Mean_Cases_10Y).toLocaleString()}</td>
                    <td class="${differenceClass}">
                        ${differenceIcon} ${Math.abs(difference).toLocaleString()}
                    </td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table>';
        return tableHTML;
    }

    // --- 8. Search and Filter Functionality ---
    function filterData() {
        const searchTerm = searchInput.value.toLowerCase();
        const riskFilter = document.getElementById('riskFilter').value;
        
        let filteredData = fullData.filter(country => {
            const matchesSearch = country.CountryCode.toLowerCase().includes(searchTerm);
            const matchesRisk = riskFilter === '' || country.Risk_Level === riskFilter;
            return matchesSearch && matchesRisk;
        });
        
        renderDataTable(filteredData);
    }

    // Add event listeners for search and filter
    searchInput.addEventListener('input', filterData);
    riskFilter.addEventListener('change', filterData);

    // --- 9. Enhanced Chart Theme Updates ---
    function updateChartTheme(theme) {
        const textColor = theme === 'dark' ? 'rgba(226, 232, 240, 0.8)' : 'rgba(255, 255, 255, 0.8)';
        const gridColor = theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.2)';

        [barChart, forecastVsHistoryChart, regionalRiskChart].forEach(chart => {
            if (chart && chart.options.scales) {
                // Update x-axis
                if (chart.options.scales.x) {
                    chart.options.scales.x.ticks = chart.options.scales.x.ticks || {};
                    chart.options.scales.x.grid = chart.options.scales.x.grid || {};
                    chart.options.scales.x.ticks.color = textColor;
                    chart.options.scales.x.grid.color = gridColor;
                }
                
                // Update y-axis
                if (chart.options.scales.y) {
                    chart.options.scales.y.ticks = chart.options.scales.y.ticks || {};
                    chart.options.scales.y.grid = chart.options.scales.y.grid || {};
                    chart.options.scales.y.ticks.color = textColor;
                    chart.options.scales.y.grid.color = gridColor;
                }
                
                // Update legend
                if (chart.options.plugins && chart.options.plugins.legend) {
                    chart.options.plugins.legend.labels = chart.options.plugins.legend.labels || {};
                    chart.options.plugins.legend.labels.color = textColor;
                }
                
                chart.update();
            }
        });
        
        // Update pie chart legend
        if (pieChart && pieChart.options.plugins && pieChart.options.plugins.legend) {
            pieChart.options.plugins.legend.labels = pieChart.options.plugins.legend.labels || {};
            pieChart.options.plugins.legend.labels.color = textColor;
            pieChart.update();
        }
    }

    // --- 10. Add smooth scroll and entrance animations ---
    dashboardContent.style.opacity = '0';
    dashboardContent.style.transform = 'translateY(20px)';
    dashboardContent.style.transition = 'all 0.6s ease';

    // --- 11. Add some interactive features ---
    // Add hover effects to cards
    document.querySelectorAll('.glass-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
        });
    });

    // --- 12. Initialize Dashboard ---
    fetchDataAndRenderCharts();

});