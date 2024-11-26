import sqlite3
import pandas as pd
import os
from datetime import datetime

def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to database: {db_file}")
    except sqlite3.Error as e:
        print(e)
    return conn

def save_neighborhood_html(neighborhood, neighborhood_df, output_dir):
    """Generate and save the HTML file for a specific neighborhood."""
    if not neighborhood_df.empty:
        # Generate HTML for the neighborhood
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Properties in {neighborhood}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
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
                    margin-top: 20px;
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
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Properties in {neighborhood}</h1>
                <div class="metadata">
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total Records: {len(neighborhood_df)}</p>
                </div>
                {neighborhood_df.to_html(index=False, escape=False)}
            </div>
        </body>
        </html>
        """

        # Save the HTML file
        output_file = os.path.join(output_dir, f"{neighborhood.replace(' ', '_')}_properties.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"Generated HTML for neighborhood: {neighborhood}")

def generate_html_by_neighborhood(db_file, output_dir):
    """Generate HTML files for properties grouped by neighborhood and an index HTML file."""
    conn = create_connection(db_file)
    if conn is None:
        return

    try:
        # Query to get properties
        query = """
        SELECT * FROM properties
        ORDER BY neighborhood, sold_date DESC;
        """
        df = pd.read_sql_query(query, conn)

        # Group by neighborhood
        neighborhoods = df['neighborhood'].unique()
        index_data = []

        for neighborhood in neighborhoods:
            neighborhood_df = df[df['neighborhood'] == neighborhood]

            # Calculate required metrics
            avg_ft_price = (neighborhood_df['sold_price'] / neighborhood_df['square_feet']).mean() if not neighborhood_df['square_feet'].isnull().all() else 0
            total_list_price = neighborhood_df['list_price'].sum()
            total_sold_price = neighborhood_df['sold_price'].sum()
            total_price_difference = (neighborhood_df['sold_price'] - neighborhood_df['list_price']).sum()

            # Append to index data
            index_data.append({
                'neighborhood': neighborhood,
                'avg_ft_price': avg_ft_price,
                'total_list_price': total_list_price,
                'total_sold_price': total_sold_price,
                'total_price_difference': total_price_difference
            })

            # Save the neighborhood HTML using the new function
            save_neighborhood_html(neighborhood, neighborhood_df, output_dir)

        # Create index HTML file
        index_html = generate_index_html(index_data, output_dir)
        with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)

        print("Generated index HTML file.")

    except Exception as e:
        print(f"Error generating HTML: {str(e)}")
    finally:
        conn.close()

def generate_index_html(index_data, output_dir):
    """Generate an index HTML file summarizing properties by neighborhood."""
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Properties Index</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
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
                margin-top: 20px;
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Properties Index</h1>
            <table>
                <thead>
                    <tr>
                        <th>Neighborhood</th>
                        <th>Average Price per Square Foot</th>
                        <th>Total List Price</th>
                        <th>Total Sold Price</th>
                        <th>Total Price Difference</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for data in index_data:
        neighborhood_link = f"{data['neighborhood'].replace(' ', '_')}_properties.html"
        index_html += f"""
                    <tr>
                        <td><a href="{neighborhood_link}">{data['neighborhood']}</a></td>
                        <td>{data['avg_ft_price']:.2f}</td>
                        <td>{data['total_list_price']:.2f}</td>
                        <td>{data['total_sold_price']:.2f}</td>
                        <td>{data['total_price_difference']:.2f}</td>
                    </tr>
        """
    
    index_html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    return index_html

# Example usage
if __name__ == "__main__":
    DATABASE_FILE = 'db/properties.sqlite3'  # Update with your database path
    OUTPUT_DIRECTORY = 'html_data/1/'  # Update with your output directory
    generate_html_by_neighborhood(DATABASE_FILE, OUTPUT_DIRECTORY)
