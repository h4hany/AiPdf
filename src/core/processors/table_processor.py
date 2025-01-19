import logging
from typing import List, Dict, Optional, Tuple
import pdfplumber
import re

class TableProcessor:
    """Handles table extraction and processing from PDF"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
    
    def is_number(self, s: str) -> bool:
        """Check if string is a number (integer or float)"""
        try:
            float(s.replace(' ', ''))  # Remove spaces from numbers like "1 234"
            return True
        except ValueError:
            return False
    
    def clean_cell(self, cell: str) -> str:
        """Clean cell content"""
        if not cell:
            return ""
        # Remove extra whitespace and newlines
        cell = ' '.join(str(cell).split())
        return cell.strip()
    
    def extract_table_data(self, table: List[List[str]]) -> List[Dict]:
        """Extract and structure table data"""
        if not table:
            return []
            
        structured_data = []
        
        try:
            # Find header row (look for years)
            header_row_index = -1
            years = []
            
            for i, row in enumerate(table):
                year_found = False
                cleaned_row = [self.clean_cell(cell) for cell in row]
                
                for cell in cleaned_row:
                    # Look for years (2020, 2021, etc.)
                    year_matches = re.findall(r'\b20\d{2}\b', cell)
                    if year_matches:
                        years.extend(year_matches)
                        year_found = True
                
                if year_found:
                    header_row_index = i
                    break
            
            if header_row_index == -1 or not years:
                self.logger.warning("No header row with years found")
                return []
                
            # Process data rows
            for row in table[header_row_index + 1:]:
                cleaned_row = [self.clean_cell(cell) for cell in row]
                
                # Skip empty rows
                if not any(cleaned_row):
                    continue
                
                # First column is usually the metric name
                metric = cleaned_row[0]
                if not metric:
                    continue
                
                # Match values with years
                row_data = {'metric': metric}
                for i, year in enumerate(years):
                    if i + 1 < len(cleaned_row):
                        value = cleaned_row[i + 1]
                        if value and self.is_number(value):
                            row_data[year] = value
                
                if len(row_data) > 1:  # Must have at least one year-value pair
                    structured_data.append(row_data)
                    self.logger.debug(f"Extracted row data: {row_data}")
            
        except Exception as e:
            self.logger.error(f"Error extracting table data: {str(e)}")
        
        return structured_data
    
    def format_table_data(self, data: List[Dict]) -> str:
        """Format structured data into readable text"""
        formatted_text = ""
        
        for row in data:
            metric = row.get('metric', '')
            if not metric:
                continue
            
            # Add each year's value
            for key, value in row.items():
                if key != 'metric' and self.is_number(value):
                    formatted_text += f"{metric} for {key} is {value}.\n"
        
        return formatted_text
    
    def process_tables(self, pages) -> str:
        """Process tables from PDF pages"""
        try:
            all_tables_text = ""
            
            for page_num, page in enumerate(pages, 1):
                self.logger.debug(f"Processing page {page_num}")
                
                # Extract tables with custom settings
                tables = page.extract_tables({
                    'vertical_strategy': 'text',
                    'horizontal_strategy': 'text',
                    'intersection_y_tolerance': 10,
                    'intersection_x_tolerance': 10
                })
                
                if not tables:
                    continue
                
                for table_num, table in enumerate(tables, 1):
                    self.logger.debug(f"Raw table {table_num} data: {table}")
                    
                    # Extract structured data
                    structured_data = self.extract_table_data(table)
                    
                    if structured_data:
                        # Format the data
                        formatted_text = self.format_table_data(structured_data)
                        if formatted_text:
                            all_tables_text += f"\nTable {table_num} content:\n{formatted_text}\n"
            
            return all_tables_text
            
        except Exception as e:
            self.logger.error(f"Error processing tables: {str(e)}", exc_info=True)
            return "" 