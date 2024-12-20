from typing import List, Dict, Any, Optional, Union, Tuple
import sqlite3
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

from config import PROPERTIES_TYPES

TABLE_HEADER_SORTING_STYLES = f"""
    th::after {{
        content: '⇕';
        margin-left: 5px;
        opacity: 0.3;
    }}
    th.asc::after {{
        content: '↑';
        opacity: 1;
    }}
    th.desc::after {{
        content: '↓';
        opacity: 1;
    }}
    """

TABLE_HEADER_SORTING_SCRIPT = f"""
        function sortTable(table, n) {{
            var rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            switching = true;
            // Set the sorting direction to ascending
            dir = "asc";

            // Remove sorting indicators from all headers
            var headers = table.getElementsByTagName("th");
            for (i = 0; i < headers.length; i++) {{
                if (i !== n) {{
                    headers[i].classList.remove("asc", "desc");
                }}
            }}

            // Toggle direction if the same header is clicked
            if (headers[n].classList.contains("asc")) {{
                dir = "desc";
                headers[n].classList.remove("asc");
                headers[n].classList.add("desc");
            }} else {{
                headers[n].classList.remove("desc");
                headers[n].classList.add("asc");
            }}

            while (switching) {{
                switching = false;
                rows = table.rows;

                for (i = 1; i < (rows.length - 1); i++) {{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("td")[n];
                    y = rows[i + 1].getElementsByTagName("td")[n];

                    // Get the text content, handling special cases
                    let xContent = x.textContent || x.innerText;
                    let yContent = y.textContent || y.innerText;

                    // Remove currency symbols, commas, and % signs for numeric comparison
                    xContent = xContent.replace(/[$,\s%]/g, '');
                    yContent = yContent.replace(/[$,\s%]/g, '');

                    // Convert to numbers if possible
                    const xNum = !isNaN(xContent) ? parseFloat(xContent) : xContent;
                    const yNum = !isNaN(yContent) ? parseFloat(yContent) : yContent;

                    if (dir === "asc") {{
                        if ((typeof xNum === "number" && typeof yNum === "number" && xNum > yNum) ||
                            (typeof xNum !== "number" && xContent.localeCompare(yContent) > 0)) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }} else if (dir === "desc") {{
                        if ((typeof xNum === "number" && typeof yNum === "number" && xNum < yNum) ||
                            (typeof xNum !== "number" && xContent.localeCompare(yContent) < 0)) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }}
                }}

                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                }}
            }}
        }}

        function getParentTable(thElement) {{
            let parent = thElement.parentElement;
            while (parent && parent.tagName !== 'TABLE') {{
                parent = parent.parentElement;
            }}
            return parent;
        }}

        // Add click handlers to all table headers when the page loads
        document.addEventListener('DOMContentLoaded', function() {{
            var headers = document.getElementsByTagName("th");
            for (var i = 0; i < headers.length; i++) {{
                headers[i].addEventListener('click', function() {{
                    var table = getParentTable(this);
                    var columnIndex = Array.from(this.parentElement.children).indexOf(this);
                    sortTable(table, columnIndex);
                }});
            }}
        }});
    """


def create_connection(db_file: Union[str, Path]) -> Optional[sqlite3.Connection]:
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to database: {db_file}")
    except sqlite3.Error as e:
        print(e)
    return conn


def _convert_urls_to_links(df: pd.DataFrame) -> pd.DataFrame:
    """Convert URL column to clickable links"""
    if "detail_url" in df.columns:
        df["url"] = df["detail_url"].apply(
            lambda x: (f'<a href="{x}" target="_blank">View</a>' if pd.notna(x) else "")
        )
    return df


def _process_neighborhood_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Process DataFrame: select columns, add calculations, sort, and format"""
    try:
        # Define column order
        columns = [
            "url",
            "built_year",
            "avg_ft_price",
            "square_feet",
            "list_price",
            "sold_price",
            "price_difference",
            "percent_difference",
            "list_date",
            "sold_date",
            "bedrooms",
            "bathrooms",
            "street_name",
            "street_type",
            "postal_code",
            "agent",
            "office",
        ]

        # Sort by sold_date descending, putting NaT (empty dates) at the end
        df = df.copy()

        # Convert URLs to links
        df = _convert_urls_to_links(df)

        # Format numeric columns
        if "sold_price" in df.columns and "list_price" in df.columns:
            sold_price = df["sold_price"]
            list_price = df["list_price"]
            df["price_difference"] = (sold_price - list_price).round(0)
            df["percent_difference"] = (df["price_difference"] / list_price) * 100
            df["percent_difference"] = df["percent_difference"].round(
                2
            )  # Round to 2 decimal places

        # Select and reorder columns
        df = df[columns]

        return df

    except Exception as e:
        print(f"Error processing DataFrame: {str(e)}")
        return df


def _style_neighborhood_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply color styling to the DataFrame based on price comparison"""
    if "percent_difference" in df.columns:
        df["percent_difference"] = df["percent_difference"].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else ""
        )

    if "price_difference" in df.columns:
        df["price_difference"] = df.apply(
            lambda row: f'<span style="color: {"green" if row["price_difference"] < 0 else "red" if row["price_difference"] > 0 else "blue"};">{row["price_difference"]}</span>',
            axis=1,
        )

    if "avg_ft_price" in df.columns:
        df["avg_ft_price"] = df["avg_ft_price"].apply(
            lambda x: f"{x:,.2f}" if pd.notna(x) and x > 0 else ""
        )

    if "list_price" in df.columns:
        df["list_price"] = df["list_price"].apply(
            lambda x: f"{x:,}" if pd.notna(x) and x > 0 else ""
        )

    if "sold_price" in df.columns:
        df["sold_price"] = df["sold_price"].apply(
            lambda x: f"{x:,}" if pd.notna(x) and x > 0 else ""
        )

    return df


def save_neighborhood_html(
    neighborhood: str, df: pd.DataFrame, display_name: str, output_dir: Union[str, Path]
) -> str:
    """Generate and save the HTML file for a specific neighborhood."""
    if not df.empty:

        # Process DataFrame
        df = _process_neighborhood_dataframe(df)

        # Style DataFrame
        df = _style_neighborhood_dataframe(df)

        # Generate HTML with sorting functionality
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Properties of {display_name} in {neighborhood}</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                }}
                .metadata {{
                    margin: 0;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-bottom: 1px solid #ddd;
                }}
                .container {{
                    width: 100%;
                    margin: 0;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 0;
                    font-size: 14px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                    white-space: nowrap;
                }}
                th {{
                    background-color: #f2f2f2;
                    position: sticky;
                    top: 0;
                    z-index: 1;
                    font-weight: bold;
                    cursor: pointer;
                    user-select: none;
                }}
                th:hover {{
                    background-color: #e0e0e0;
                }}
                {TABLE_HEADER_SORTING_STYLES}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                td:nth-child(n) {{
                    text-align: center;
                }}
                a {{
                    color: #0066cc;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .scroll-wrapper {{
                    width: 100%;
                    overflow-x: auto;
                    position: relative;
                }}
                /* Specific column alignments */
                td:nth-child(n+3):nth-child(-n+8) {{
                    text-align: right;
                }}  /* numeric columns */
                /* Right align the last two columns */
                td:nth-last-child(1),
                td:nth-last-child(2) {{
                    text-align: left;
                }}
            </style>
            <script>
            {TABLE_HEADER_SORTING_SCRIPT}
            </script>
        </head>
        <body>
            <h1>Properties of {display_name} in {neighborhood}</h1>
            <div class="metadata">
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Records: {len(df)}</p>
            </div>
            <div class="scroll-wrapper">
                {df.to_html(index=False, border=1, classes='dataframe', escape=False)}
            </div>
        </body>
        </html>
        """

        # Save the HTML file
        filename = neighborhood.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{filename}_properties.html"
        output_file = os.path.join(output_dir, filename)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Generated HTML for neighborhood: {neighborhood}")

        return filename


def calculate_decade_stats_for_neighborhood(
    conn: sqlite3.Connection,
    neighborhood: str,
    table_name: str
) -> Tuple[str, Dict[str, Any]]:
    """Calculate decade statistics for a specific neighborhood and return HTML and chart data"""
    query = f"""
    SELECT built_year, COUNT(*) as count
    FROM {table_name}
    WHERE neighborhood = ? AND built_year IS NOT NULL
    GROUP BY built_year
    ORDER BY built_year
    """

    df = pd.read_sql_query(query, conn, params=[neighborhood])

    # Group by decades
    decades = {}
    current_year = datetime.now().year

    # Create decade ranges from 1950 to current year
    start_year = 1950
    while start_year <= current_year:
        decade_end = start_year + 9
        decade = f"{start_year}-{decade_end}"
        mask = df["built_year"].between(start_year, decade_end)
        count = df[mask]["count"].sum()
        if count > 0:  # Only include decades with properties
            decades[decade] = int(count)
        start_year += 10

    # Prepare chart data
    chart_data = {"labels": list(decades.keys()), "data": list(decades.values())}

    # Create HTML table for the popup
    total_properties = sum(decades.values())

    html = f"""
    <div class="decade-stats">
        <h3>Built Years Statistics for {neighborhood}</h3>
        <div class="chart-container">
            <canvas id="decadeChart_{neighborhood.replace(' ', '_')}"></canvas>
        </div>
        <table>
            <tr>
                <th>Decade</th>
                <th>Number of Properties</th>
                <th>Percentage</th>
            </tr>
    """

    for decade, count in decades.items():
        percentage = (count / total_properties) * 100
        html += f"""
            <tr>
                <td>{decade}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
        """

    html += """
        </table>
    </div>
    """
    return html, chart_data


def get_area_coordinates(conn: sqlite3.Connection) -> Dict[str, Dict[str, float]]:
    """Get coordinates for all areas from the database"""
    query = """
    SELECT area_name, latitude, longitude
    FROM area_coordinates
    """
    cursor = conn.cursor()
    coordinates = {}
    try:
        for row in cursor.execute(query):
            safe_neighborhood = row[0].replace(" ", "_").replace("/", "_")
            coordinates[safe_neighborhood] = {
                'lat': row[1],
                'lng': row[2]
            }
    except sqlite3.Error as e:
        print(f"Error getting coordinates: {e}")
    return coordinates


def save_index_html(
    index_data: List[Dict[str, Union[str, float]]],
    display_name: str,
    output_dir: Union[str, Path],
    conn: sqlite3.Connection,
    table_name: str
) -> None:
    """Generate an index HTML file summarizing properties by neighborhood."""
    
    # Get coordinates for all areas
    area_coordinates = get_area_coordinates(conn)
    
    # Generate decade stats for each neighborhood
    neighborhood_stats = {}
    chart_data = {}
    map_data = []
    
    for data in index_data:
        neighborhood = data['neighborhood']
        safe_neighborhood = neighborhood.replace(" ", "_").replace("/", "_")

        stats_html, decade_data = calculate_decade_stats_for_neighborhood(
            conn, neighborhood, table_name
        )
        neighborhood_stats[neighborhood] = stats_html
        chart_data[safe_neighborhood] = decade_data
        
        # Add map data if coordinates exist
        if safe_neighborhood in area_coordinates:
            map_data.append({
                'name': neighborhood,
                'coordinates': area_coordinates[safe_neighborhood],
                'property_count': int(data['property_count']),
                'avg_ft_price': float(data['avg_ft_price']),
                'total_list_price': float(data['total_list_price']),
                'total_sold_price': float(data['total_sold_price']),
                'total_price_difference': float(data['total_price_difference']),
                'total_percent_difference': float(data['total_percent_difference'])
            })
    
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Properties Index</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .metadata {{
                margin: 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }}
            .container {{
                max-width: 100%;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            {TABLE_HEADER_SORTING_STYLES}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            tr:hover {{
                background-color: #f2f2f2;
            }}
            td:nth-child(n) {{
                text-align: center;
            }}
            /* Specific column alignments */
            td:nth-child(n+3):nth-child(-n+8) {{
                text-align: right;
            }}  /* numeric columns */

            /* Popup styles */
            .popup-overlay {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 1000;
            }}

            .popup-content {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                max-width: 80%;
                max-height: 80%;
                overflow-y: auto;
            }}

            .decade-stats table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}

            .decade-stats th, .decade-stats td {{
                padding: 8px;
                text-align: center;
                border: 1px solid #ddd;
            }}

            .decade-stats th {{
                background-color: #f5f5f5;
            }}

            .close-popup {{
                position: absolute;
                top: 10px;
                right: 10px;
                cursor: pointer;
                font-size: 20px;
            }}

            .built-years-link {{
                cursor: pointer;
                color: #0066cc;
                text-decoration: underline;
            }}

            .chart-container {{
                width: 100%;
                height: 300px;
                margin-bottom: 20px;
            }}
            
            .popup-content {{
                min-width: 600px;
            }}
            
            #map-container {{
                height: 500px;
                width: 100%;
                margin: 20px 0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }}
            
            .leaflet-popup-content {{
                min-width: 200px;
            }}

            .permanent-popup .leaflet-popup-content-wrapper {{
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                padding: 5px;
            }}
            
            .permanent-popup .leaflet-popup-tip-container {{
                visibility: hidden;
            }}

            #detailed-popup-container {{
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 1000;
                max-width: 90%;
                max-height: 90%;
                overflow-y: auto;
            }}

            .detail-table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }}

            .detail-table td {{
                padding: 8px;
                border: 1px solid #ddd;
            }}

            .detail-table td:first-child {{
                font-weight: bold;
                background-color: #f5f5f5;
                width: 40%;
            }}

            .close-button {{
                position: absolute;
                top: 10px;
                right: 10px;
                cursor: pointer;
                font-size: 24px;
                color: #666;
            }}

            .close-button:hover {{
                color: #000;
            }}
        </style>
        <script>
            const chartData = {str(chart_data).replace("'", '"')};
            const mapData = {str(map_data).replace("'", '"')};
            
            function createChart(neighborhood) {{
                const safe_neighborhood = neighborhood.replace(' ', '_');
                const ctx = document.getElementById('decadeChart_' + safe_neighborhood);
                
                // Destroy existing chart if it exists
                if (window.decadeCharts && window.decadeCharts[safe_neighborhood]) {{
                    window.decadeCharts[safe_neighborhood].destroy();
                }}
                
                // Create new chart
                if (!window.decadeCharts) window.decadeCharts = {{}};
                
                // Generate random colors for each decade
                const colors = chartData[safe_neighborhood].labels.map(() => {{
                    const r = Math.floor(Math.random() * 200 + 55); // 55-255
                    const g = Math.floor(Math.random() * 200 + 55); // 55-255
                    const b = Math.floor(Math.random() * 200 + 55); // 55-255
                    return {{
                        backgroundColor: `rgba(${{r}}, ${{g}}, ${{b}}, 0.5)`,
                        borderColor: `rgba(${{r}}, ${{g}}, ${{b}}, 1)`
                    }};
                }});
                
                window.decadeCharts[safe_neighborhood] = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: chartData[safe_neighborhood].labels,
                        datasets: [{{
                            label: 'Number of Properties',
                            data: chartData[safe_neighborhood].data,
                            backgroundColor: colors.map(c => c.backgroundColor),
                            borderColor: colors.map(c => c.borderColor),
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{
                                    display: true,
                                    text: 'Number of Properties'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'Decade'
                                }}
                            }}
                        }},
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Properties by Decade'
                            }},
                            legend: {{
                                display: false
                            }}
                        }}
                    }}
                }});
            }}

            function showDecadeStats(neighborhood) {{
                const safe_neighborhood = neighborhood.replace(' ', '_');
                document.getElementById('statsContent_' + safe_neighborhood).style.display = 'block';
                createChart(neighborhood);
            }}
            
            function closePopup(neighborhood) {{
                const safe_neighborhood = neighborhood.replace(' ', '_');
                document.getElementById('statsContent_' + safe_neighborhood).style.display = 'none';
            }}
            
            // Close popup when clicking outside
            window.onclick = function(event) {{
                if (event.target.classList.contains('popup-overlay')) {{
                    event.target.style.display = 'none';
                }}
            }}
            
            function initMap() {{
                // Initialize the map centered on Calgary
                const map = L.map('map-container').setView([51.0447, -114.0719], 11);
                
                // Add OpenStreetMap tiles
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                
                // Add markers and permanent popups for each neighborhood
                mapData.forEach(area => {{
                    // Create initial popup content with clickable numbers
                    const popupContent = `
                        <div style="text-align: center; min-width: 0px; margin: 0px 0px;">
                            <div onclick="showDetailedPopup('${{area.name}}', ${{JSON.stringify(area).replace(/"/g, '&quot;')}})" 
                                 style="cursor: pointer; color: #0066cc;">
                                <strong>${{area.name}}</strong><br>
                                Properties: ${{area.property_count}}<br>
                                Avg. Price/sqft: $${{area.avg_ft_price.toFixed(2)}}
                            </div>
                        </div>
                    `;
                    
                    // Create and bind a permanent popup
                    const popup = L.popup({{
                        closeButton: false,    // Remove close button
                        closeOnClick: false,   // Don't close when clicking elsewhere
                        autoClose: false,      // Don't close when another popup opens
                        className: 'permanent-popup'  // Custom CSS class for styling
                    }})
                        .setLatLng([area.coordinates.lat, area.coordinates.lng])
                        .setContent(popupContent)
                        .addTo(map);
                }});
            }}

            function showDetailedPopup(areaName, areaData) {{
                // Create detailed popup content as a table
                const detailedContent = `
                    <div class="detailed-popup">
                        <h3>${{areaName}}</h3>
                        <table class="detail-table">
                            <tr>
                                <td>Neighborhood</td>
                                <td>${{areaName}}</td>
                            </tr>
                            <tr>
                                <td>Property Count</td>
                                <td>${{areaData.property_count}}</td>
                            </tr>
                            <tr>
                                <td>Average Price/sqft</td>
                                <td>$${{areaData.avg_ft_price.toFixed(2)}}</td>
                            </tr>
                            <tr>
                                <td>Total List Price</td>
                                <td>$${{areaData.total_list_price.toLocaleString()}}</td>
                            </tr>
                            <tr>
                                <td>Total Sold Price</td>
                                <td>$${{areaData.total_sold_price.toLocaleString()}}</td>
                            </tr>
                            <tr>
                                <td>Total Price Difference</td>
                                <td style="color: ${{areaData.total_price_difference < 0 ? 'green' : 'red'}}">
                                    ${{areaData.total_price_difference.toLocaleString()}}
                                </td>
                            </tr>
                            <tr>
                                <td>Total Percent Difference</td>
                                <td style="color: ${{areaData.total_percent_difference < 0 ? 'green' : 'red'}}">
                                    ${{areaData.total_percent_difference.toFixed(2)}}%
                                </td>
                            </tr>
                        </table>
                        <div class="close-button" onclick="closeDetailedPopup()">×</div>
                    </div>
                `;

                // Create or update the detailed popup container
                let detailsContainer = document.getElementById('detailed-popup-container');
                if (!detailsContainer) {{
                    detailsContainer = document.createElement('div');
                    detailsContainer.id = 'detailed-popup-container';
                    document.body.appendChild(detailsContainer);
                }}
                detailsContainer.innerHTML = detailedContent;
                detailsContainer.style.display = 'block';
            }}

            function closeDetailedPopup() {{
                const container = document.getElementById('detailed-popup-container');
                if (container) {{
                    container.style.display = 'none';
                }}
            }}

            // Initialize map when document is ready
            document.addEventListener('DOMContentLoaded', function() {{
                initMap();
            }});

            {TABLE_HEADER_SORTING_SCRIPT}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Properties of {display_name} Index</h1>
            <div class="metadata">
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Neighborhoods: {len(index_data)}</p>
            </div>
            
            <!-- Add map container -->
            <div id="map-container"></div>
            
            <!-- Existing table -->
            <table>
                <thead>
                    <tr>
                        <th>Neighborhood</th>
                        <th>Built Years</th>
                        <th>Property Count</th>
                        <th>Average Price per Square Foot</th>
                        <th>Total List Price</th>
                        <th>Total Sold Price</th>
                        <th>Total Price Difference</th>
                        <th>Total Percent Difference</th>
                    </tr>
                </thead>
                <tbody>
    """

    for data in index_data:
        neighborhood = data["neighborhood"]
        safe_neighborhood = neighborhood.replace(" ", "_").replace("/", "_")
        diff = data["total_price_difference"]
        color = f'{"green" if diff < 0 else "red" if diff > 0 else "blue"}'

        index_html += f"""
                    <tr>
                        <td><a href="{data['filename']}">{neighborhood}</a></td>
                        <td>
                            <span class="built-years-link" onclick="showDecadeStats('{safe_neighborhood}')">
                                Click to show built years
                            </span>
                        </td>
                        <td>{data['property_count']}</td>
                        <td>{data['avg_ft_price']:,.2f}</td>
                        <td>{data['total_list_price']:,.2f}</td>
                        <td>{data['total_sold_price']:,.2f}</td>
                        <td><span style="color: {color}">{data['total_price_difference']:,.2f}</span></td>
                        <td><span style="color: {color}">{data['total_percent_difference']:,.2f}%</span></td>
                    </tr>
        """

    index_html += """
                </tbody>
            </table>
        </div>
        """

    for data in index_data:
        neighborhood = data["neighborhood"]
        safe_neighborhood = neighborhood.replace(" ", "_").replace("/", "_")
        index_html += f"""
                    <!-- Popup for this neighborhood -->
                    <div id="statsContent_{safe_neighborhood}" class="popup-overlay">
                        <div class="popup-content">
                            <span class="close-popup" onclick="closePopup('{safe_neighborhood}')">&times;</span>
                            {neighborhood_stats[neighborhood]}
                        </div>
                    </div>
        """

    index_html += """
    </body>
    </html>
    """

    # Save the index HTML file
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Generated index HTML file of {display_name}.")


def generate_htmls(
    conn: sqlite3.Connection,
    property_type: Dict[str, str],
    output_dir: Union[str, Path],
) -> None:
    """Generate HTML files for properties grouped by neighborhood and an index HTML file."""
    os.makedirs(output_dir, exist_ok=True)

    table_name = property_type["name"]
    display_name = property_type["display-name"]

    # Query to get properties
    query = f"""
    SELECT * FROM {table_name}
    ORDER BY neighborhood, sold_date DESC;
    """
    df = pd.read_sql_query(query, conn)

    # Group by neighborhood
    neighborhoods = df["neighborhood"].unique()
    index_data = []

    for neighborhood in neighborhoods:
        neighborhood_df = df[df["neighborhood"] == neighborhood]

        # Save the neighborhood HTML using the new function
        filename = save_neighborhood_html(
            neighborhood, neighborhood_df, display_name, output_dir
        )

        # Calculate required metrics
        property_count = neighborhood_df["id"].count()
        avg_ft_price = (
            (neighborhood_df["sold_price"] / neighborhood_df["square_feet"]).mean()
            if not neighborhood_df["square_feet"].isnull().all()
            else 0
        )
        total_list_price = neighborhood_df["list_price"].sum()
        total_sold_price = neighborhood_df["sold_price"].sum()
        total_price_difference = total_sold_price - total_list_price
        total_percent_difference = 100 * total_price_difference / total_list_price

        # Append to index data
        index_data.append(
            {
                "property_count": property_count,
                "neighborhood": neighborhood,
                "avg_ft_price": avg_ft_price,
                "total_list_price": total_list_price,
                "total_sold_price": total_sold_price,
                "total_price_difference": total_price_difference,
                "total_percent_difference": total_percent_difference,
                "filename": filename,
            }
        )

    # Save the index HTML using the new function
    save_index_html(index_data, display_name, output_dir, conn, table_name)


def save_global_index_html(output_dir: Union[str, Path]) -> None:
    """Generate an index HTML file summarizing properties by neighborhood."""
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Propertie Types Index</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .metadata {{
                margin: 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            tr:hover {{
                background-color: #f2f2f2;
            }}
            td:nth-child(n) {{
                text-align: center;
            }}
            /* Specific column alignments */
            td:nth-child(n+2):nth-child(-n+6) {{
                text-align: right;
            }}  /* numeric columns */
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Properties Index</h1>
            <div class="metadata">
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Property Type</th>
                    </tr>
                </thead>
                <tbody>
    """

    for property_name, property_type in PROPERTIES_TYPES.items():
        index_html += f"""
                    <tr>
                        <td><a href="{property_name}/index.html">{property_type['display-name']}</a></td>
                    </tr>
        """

    index_html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    # Save the index HTML file
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print("Generated index HTML file.")


def generate_all_htmls(db_file: Union[str, Path], output_dir: Union[str, Path]) -> None:
    """Generate HTML files for all property types."""
    conn = create_connection(db_file)
    if conn is None:
        return

    try:
        for property_name, property_type in PROPERTIES_TYPES.items():
            dir_name = os.path.join(output_dir, property_name)
            generate_htmls(conn, property_type, dir_name)

        save_global_index_html(output_dir)
    except Exception as e:
        print(f"Error generating HTML: {str(e)}")
    finally:
        conn.close()


# Example usage
if __name__ == "__main__":
    DATABASE_FILE = "db/properties.sqlite3"  # Update with your database path
    OUTPUT_DIRECTORY = "html_data/v2"  # Update with your output directory
    generate_all_htmls(DATABASE_FILE, OUTPUT_DIRECTORY)
