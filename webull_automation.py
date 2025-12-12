"""
Webull Canada Trade Automation Solutions
Since Webull CA doesn't have a public API and email notifications aren't available,
this module provides alternative methods to automatically track trades.
"""
import os
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

class WebullCSVAutomation:
    """
    Automated CSV export from Webull website
    This uses browser automation to log in and download trade history CSV
    """
    
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set download directory
        download_dir = os.path.join(os.getcwd(), 'webull_downloads')
        os.makedirs(download_dir, exist_ok=True)
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def login_and_download_csv(self, start_date: datetime = None, end_date: datetime = None) -> str:
        """
        Login to Webull and download trade history CSV
        Returns path to downloaded CSV file
        """
        if not self.driver:
            self.setup_driver()
        
        try:
            # Navigate to Webull login page
            self.driver.get("https://www.webull.com/login")
            time.sleep(2)
            
            # Enter credentials (adjust selectors based on actual Webull website)
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys(self.username)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Navigate to account/trade history page
            # Note: These selectors need to be adjusted based on actual Webull website structure
            self.driver.get("https://www.webull.com/account/trade-history")
            time.sleep(3)
            
            # Set date range if provided
            if start_date and end_date:
                # Find date picker elements and set dates
                # This will need to be customized based on Webull's actual interface
                pass
            
            # Find and click export/download CSV button
            # Note: This selector needs to be found by inspecting Webull's actual page
            export_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Export') or contains(text(), 'Download')]"))
            )
            export_button.click()
            
            # Wait for download to complete
            time.sleep(5)
            
            # Find the downloaded file
            download_dir = os.path.join(os.getcwd(), 'webull_downloads')
            files = os.listdir(download_dir)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            if csv_files:
                # Get the most recently downloaded file
                csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
                return os.path.join(download_dir, csv_files[0])
            
            return None
            
        except Exception as e:
            print(f"Error downloading CSV from Webull: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
    
    def cleanup(self):
        """Close browser driver"""
        if self.driver:
            self.driver.quit()


class WebullOrderAssistantParser:
    """
    Alternative: Parse order notifications from Webull's in-app order assistant
    This would require:
    1. Mobile app automation (using Appium)
    2. Or browser extension to intercept network requests
     """
    
    @staticmethod
    def parse_order_message(message_text: str) -> Dict:
        """
        Parse order notification text from Webull order assistant
        Example format: "Your order for 10 AAPL CALL 150 12/20/2024 @ $2.50 has been filled"
        """
        # This is a placeholder - actual parsing would depend on Webull's message format
        trade_data = {
            'symbol': '',
            'quantity': 0,
            'price': 0,
            'action': '',
            'date': datetime.now().isoformat(),
            'trade_type': 'OPTION',
            'option_type': 'CALL',
            'strike': 0,
            'expiration': ''
        }
        
        # Add parsing logic based on actual Webull message format
        # This would need to be customized after seeing actual message examples
        
        return trade_data


class WebullCSVWatcher:
    """
    Watch for new CSV files in a directory and auto-import
    User can set up a folder action (macOS) or scheduled task to export CSV to watched folder
    """
    
    def __init__(self, watch_directory: str):
        self.watch_directory = watch_directory
        self.processed_files = set()
        os.makedirs(watch_directory, exist_ok=True)
    
    def check_for_new_files(self) -> List[str]:
        """Check for new CSV files in watch directory"""
        if not os.path.exists(self.watch_directory):
            return []
        
        files = [f for f in os.listdir(self.watch_directory) if f.endswith('.csv')]
        new_files = [f for f in files if f not in self.processed_files]
        return [os.path.join(self.watch_directory, f) for f in new_files]
    
    def mark_as_processed(self, filepath: str):
        """Mark a file as processed"""
        filename = os.path.basename(filepath)
        self.processed_files.add(filename)


def create_webull_csv_parser():
    """
    Enhanced CSV parser specifically for Webull Canada exports
    Handles various Webull CSV formats
    """
    def parse_webull_csv(filepath: str) -> List[Dict]:
        """Parse Webull CSV export into standard trade format"""
        trades = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)
                delimiter = ',' if sample.count(',') > sample.count(';') else ';'
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    # Webull CSV columns may vary, try common variations
                    symbol = row.get('Symbol') or row.get('Ticker') or row.get('symbol', '')
                    action = row.get('Action') or row.get('Side') or row.get('Type', '').upper()
                    quantity = float(row.get('Quantity') or row.get('Qty') or row.get('Shares', 0))
                    price = float(row.get('Price') or row.get('Fill Price') or row.get('Avg Price', 0))
                    date_str = row.get('Date') or row.get('Time') or row.get('Execution Time', '')
                    fee = float(row.get('Commission') or row.get('Fee') or row.get('Transaction Fee', 0))
                    
                    # Parse date
                    try:
                        # Try various date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d']:
                            try:
                                trade_date = datetime.strptime(date_str, fmt)
                                break
                            except:
                                continue
                        else:
                            trade_date = datetime.now()
                    except:
                        trade_date = datetime.now()
                    
                    # Determine action
                    if 'BUY' in action.upper() or 'OPEN' in action.upper():
                        action = 'BUY'
                    elif 'SELL' in action.upper() or 'CLOSE' in action.upper():
                        action = 'SELL'
                    else:
                        action = 'BUY'  # Default
                    
                    # Parse options if present
                    trade_type = 'STOCK'
                    option_type = None
                    strike = None
                    expiration = None
                    
                    # Check if symbol contains option info
                    # Webull format: "AAPL 241220C150" or "AAPL CALL 150 12/20/2024"
                    if ' ' in symbol or 'CALL' in symbol.upper() or 'PUT' in symbol.upper():
                        # Try to parse option details
                        parts = symbol.split()
                        if len(parts) >= 2:
                            base_symbol = parts[0]
                            # Check for option indicators
                            if 'CALL' in symbol.upper() or 'C' in parts[-1]:
                                trade_type = 'OPTION'
                                option_type = 'CALL'
                            elif 'PUT' in symbol.upper() or 'P' in parts[-1]:
                                trade_type = 'OPTION'
                                option_type = 'PUT'
                            
                            symbol = base_symbol
                    
                    trade = {
                        'symbol': symbol,
                        'action': action,
                        'quantity': abs(quantity),
                        'price': price,
                        'date': trade_date.isoformat(),
                        'trade_type': trade_type,
                        'option_type': option_type,
                        'strike': strike,
                        'expiration': expiration,
                        'transaction_fee': fee,
                        'brokerage': 'Webull',
                        'source': 'csv_import'
                    }
                    
                    trades.append(trade)
            
            return trades
            
        except Exception as e:
            print(f"Error parsing Webull CSV: {e}")
            return []
    
    return parse_webull_csv


