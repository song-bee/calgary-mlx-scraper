import sqlite3
import pandas as pd
import os
from datetime import datetime

from config import PROPERTIES_TYPES


def create_connection(db_file):
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


def save_neighborhood_html(neighborhood, neighborhood_df, display_name, output_dir):
    """Generate and save the HTML file for a specific neighborhood."""
    if not neighborhood_df.empty:

        # Process DataFrame
        df = _process_neighborhood_dataframe(neighborhood_df)

        # Style DataFrame
        df = _style_neighborhood_dataframe(df)

        # Generate HTML for the neighborhood
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
                }}
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


def save_index_html(index_data, display_name, output_dir):
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
            <h1>Properties of {display_name} Index</h1>
            <div class="metadata">
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Neighborhoods: {len(index_data)}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Neighborhood</th>
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
        diff = data["total_price_difference"]
        color = f'{"green" if diff < 0 else "red" if diff > 0 else "blue"}'

        index_html += f"""
                    <tr>
                        <td><a href="{data['filename']}">{data['neighborhood']}</a></td>
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
    </body>
    </html>
    """
    # Save the index HTML file
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"Generated index HTML file of {display_name}.")


def generate_htmls(conn, property_type, output_dir):
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
    save_index_html(index_data, display_name, output_dir)


def save_global_index_html(output_dir):
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


def generate_all_htmls(db_file, output_dir):
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
