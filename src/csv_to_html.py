import pandas as pd
import os
from datetime import datetime
from typing import Dict

class CSVToHTML:
    def __init__(self):
        # Base directories
        self.data_dir = "data"
        self.base_html_dir = "html_data"
        
        # Create timestamp-based subdirectory for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(self.base_html_dir, self.timestamp)
        
        # Create directory structure
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directory structure"""
        try:
            # Create base HTML directory
            os.makedirs(self.base_html_dir, exist_ok=True)
            
            # Create timestamp subdirectory
            os.makedirs(self.output_dir, exist_ok=True)
            
            print(f"Created output directory: {self.output_dir}")
            
        except Exception as e:
            print(f"Error creating directories: {str(e)}")
            raise

    def _convert_urls_to_links(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert URL column to clickable links"""
        if 'detail_url' in df.columns:
            df['url'] = df['detail_url'].apply(lambda x: f'<a href="{x}" target="_blank">View</a>' if pd.notna(x) else '')
        return df

    def _add_avg_ft_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add average price per square foot column"""
        try:
            # Convert price and square_feet to numeric, handling any non-numeric values
            df['sold_price'] = pd.to_numeric(df['sold_price'], errors='coerce')
            df['square_feet'] = pd.to_numeric(df['square_feet'], errors='coerce')
            
            # Calculate price per square foot
            # Only calculate where both price and square feet are valid numbers and greater than 0
            mask = (df['sold_price'] > 0) & (df['square_feet'] > 0)
            df['avg_ft_price'] = 0.0  # Initialize column
            df.loc[mask, 'avg_ft_price'] = df.loc[mask, 'sold_price'] / df.loc[mask, 'square_feet']
            
            # Format to 2 decimal places
            df['avg_ft_price'] = df['avg_ft_price'].round(2)
            
            return df
        except Exception as e:
            print(f"Error calculating average price per square foot: {str(e)}")
            return df

    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process DataFrame: select columns, add calculations, sort, and format"""
        try:
            # Define column order
            columns = [
                'url',
                'avg_ft_price',     # Calculated field
                'square_feet',
                'list_price',
                'sold_price',
                'list_date',
                'sold_date',
                'bedrooms',
                'bathrooms',
                'street_number',
                'street_name',
                'street_direction',
                'street_type',
                'postal_code',
                'agent',
                'office'
            ]
            
            # Add average price per square foot
            df = self._add_avg_ft_price(df)
            
            # Sort by sold_date descending, putting NaT (empty dates) at the end
            df = df.sort_values(by='sold_date', ascending=False, na_position='last')
            
            # Convert URLs to links
            df = self._convert_urls_to_links(df)
            
            # Format numeric columns
            if 'avg_ft_price' in df.columns:
                df['avg_ft_price'] = df['avg_ft_price'].apply(lambda x: f'${x:,.2f}' if pd.notna(x) and x > 0 else '')
            
            # Select and reorder columns
            df = df[columns]
            
            return df
            
        except Exception as e:
            print(f"Error processing DataFrame: {str(e)}")
            return df

    def convert_file(self, filename: str) -> None:
        """Convert a single CSV file to HTML table format"""
        try:
            # Read CSV file
            df = pd.read_csv(os.path.join(self.data_dir, filename))
            
            # Process DataFrame
            df = self._process_dataframe(df)
            
            # Create HTML content
            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{filename}</title>
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
                        text-align: left;
                        white-space: nowrap;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        position: sticky;
                        top: 0;
                        z-index: 1;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    td:nth-child(n+8) {{  /* Numeric columns alignment */
                        text-align: right;
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
                    td:nth-child(1) {{
                        text-align: center;
                    }}  /* detail_url */
                    td:nth-child(n+2):nth-child(-n+5) {{
                        text-align: right;
                    }}  /* numeric columns */
                    td:nth-child(n+6):nth-child(-n+7) {{
                        text-align: center;
                    }}  /* date columns */
                    td:nth-child(n+8):nth-child(-n+9) {{
                        text-align: center;
                    }}  /* bedrooms, bathrooms */
                </style>
            </head>
            <body>
                <div class="metadata">
                    <p>Source file: {filename}</p>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total records: {len(df)}</p>
                </div>
                <div class="scroll-wrapper">
                    {df.to_html(index=False, border=1, classes='dataframe', escape=False, 
                              float_format=lambda x: '${:,.2f}'.format(x) if pd.notna(x) else '')}
                </div>
            </body>
            </html>
            """
            
            # Save HTML file
            output_filename = filename.replace('.csv', '.html')
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
                
            print(f"Converted {filename} to HTML: {output_path}")
            
        except Exception as e:
            print(f"Error converting {filename}: {str(e)}")

    def _create_index_html(self) -> None:
        """Create an index.html file linking to all generated HTML files"""
        try:
            # Get list of generated HTML files
            html_files = sorted([f for f in os.listdir(self.output_dir) 
                               if f.endswith('.html')])
            
            if not html_files:
                return
            
            # Create index HTML content
            index_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Calgary Property Data Index</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #333;
                        margin-bottom: 20px;
                        padding-bottom: 10px;
                        border-bottom: 2px solid #eee;
                    }}
                    .metadata {{
                        background-color: #f8f9fa;
                        padding: 10px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }}
                    .file-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 15px;
                        margin-top: 20px;
                    }}
                    .file-link {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 4px;
                        border: 1px solid #dee2e6;
                        text-decoration: none;
                        color: #333;
                        transition: all 0.2s ease;
                    }}
                    .file-link:hover {{
                        background-color: #e9ecef;
                        border-color: #adb5bd;
                        transform: translateY(-2px);
                    }}
                    .timestamp {{
                        color: #666;
                        font-size: 0.9em;
                        margin-top: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Calgary Property Data</h1>
                    <div class="metadata">
                        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>Total Files: {len(html_files)}</p>
                    </div>
                    <div class="file-grid">
            """
            
            # Add links to each file
            for filename in html_files:
                # Extract area and year from filename
                # Expected format: calgary_properties_TYPE_CODE_YEAR.html
                parts = filename.replace('.html', '').split('_')
                if len(parts) >= 5:
                    area_type = parts[2]
                    area_code = parts[3]
                    year = parts[4]
                    
                    display_name = f"{area_type.title()} {area_code} ({year})"
                else:
                    display_name = filename
                
                index_html += f"""
                        <a href="{filename}" class="file-link">
                            <div>{display_name}</div>
                            <div class="timestamp">{datetime.fromtimestamp(os.path.getmtime(os.path.join(self.output_dir, filename))).strftime('%Y-%m-%d %H:%M')}</div>
                        </a>
                """
            
            index_html += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Save index.html in the output directory
            index_path = os.path.join(self.output_dir, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_html)
                
            print(f"Created index.html at: {index_path}")
            
        except Exception as e:
            print(f"Error creating index.html: {str(e)}")

    def convert_all_files(self) -> None:
        """Convert all CSV files and create index"""
        csv_files = [f for f in os.listdir(self.data_dir) 
                    if f.endswith('.csv') and f.startswith('calgary_properties_')]
        
        if not csv_files:
            print("No CSV files found to convert")
            return
        
        print(f"Found {len(csv_files)} CSV files to convert")
        
        for filename in csv_files:
            self.convert_file(filename)
        
        # Create index.html after all files are converted
        self._create_index_html()
        
        print(f"\nConversion complete. HTML files are in: {self.output_dir}")
        print(f"Total files converted: {len(csv_files)}")

def main():
    try:
        converter = CSVToHTML()
        converter.convert_all_files()
    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main() 