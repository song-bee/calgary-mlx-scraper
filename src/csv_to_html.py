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
            df['detail_url'] = df['detail_url'].apply(lambda x: f'<a href="{x}" target="_blank">View</a>' if pd.notna(x) else '')
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
                'url',              # Will be shown as detail_url
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
            
            # Convert sold_date to datetime for sorting
            df['sold_date'] = pd.to_datetime(df['sold_date'], errors='coerce')
            
            # Add average price per square foot
            df = self._add_avg_ft_price(df)
            
            # Sort by sold_date descending, putting NaT (empty dates) at the end
            df = df.sort_values(by='sold_date', ascending=False, na_position='last')
            
            # Format dates
            df['sold_date'] = df['sold_date'].dt.strftime('%Y-%m-%d')
            df['list_date'] = pd.to_datetime(df['list_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Convert URLs to links
            df = self._convert_urls_to_links(df)
            
            # Format numeric columns
            if 'avg_ft_price' in df.columns:
                df['avg_ft_price'] = df['avg_ft_price'].apply(lambda x: f'${x:,.2f}' if pd.notna(x) and x > 0 else '')
            
            # Select and reorder columns
            df = df[columns]
            
            # Rename columns
            df = df.rename(columns={'url': 'detail_url'})
            
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
                    td:nth-child(1) {  /* detail_url */
                        text-align: center;
                    }
                    td:nth-child(n+2):nth-child(-n+5) {  /* numeric columns */
                        text-align: right;
                    }
                    td:nth-child(n+6):nth-child(-n+7) {  /* date columns */
                        text-align: center;
                    }
                    td:nth-child(n+8):nth-child(-n+9) {  /* bedrooms, bathrooms */
                        text-align: center;
                    }
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

    def convert_all_files(self) -> None:
        """Convert all CSV files in the data directory"""
        csv_files = [f for f in os.listdir(self.data_dir) 
                    if f.endswith('.csv') and f.startswith('calgary_properties_')]
        
        if not csv_files:
            print("No CSV files found to convert")
            return
        
        print(f"Found {len(csv_files)} CSV files to convert")
        
        for filename in csv_files:
            self.convert_file(filename)
        
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