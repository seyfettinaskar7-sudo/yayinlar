import json
import re
import os
import time
from urllib.parse import urljoin
import cloudscraper

def download_stream_manifest(stream_id, referer, country, subdivision, folder_name):
    """
    Downloads and processes M3U8 stream manifest from Galata.ai
    
    Args:
        stream_id (str): The stream ID to fetch
        referer (str): The referer URL to use in the request
        country (str): Country code (e.g., 'TR')
        subdivision (str): Subdivision code (e.g., '53')
        folder_name (str): The folder name for the location
    
    Returns:
        dict: A dictionary with 'success', 'message', and 'file_path' keys
    """
    try:
        # Create the folder structure: country/subdivision/folder_name
        folder_path = os.path.join(country, str(subdivision), folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        # Initialize cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Build the embed URL
        embed_url = f'https://embed.galata.ai/embed/{stream_id}'
        
        print(f"[INFO] Fetching embed page: {embed_url}")
        print(f"[INFO] Using referer: {referer}")
        
        # Step 1: Send request to embed page with referer
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': referer,
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'iframe',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
        }
        
        response = scraper.get(embed_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {
                'success': False,
                'message': f'Failed to fetch embed page. HTTP Status: {response.status_code}',
                'file_path': None
            }
        
        print(f"[INFO] Successfully fetched embed page ({len(response.text)} bytes)")
        
        # Step 2: Find M3U8 URL with regex
        m3u8_patterns = [
            r'src="([^"]*\.m3u8[^"]*)"',  # Standard src attribute
            r"src='([^']*\.m3u8[^']*)'",  # Single quoted src
            r'"(https?://[^"]*\.m3u8[^"]*)"',  # Any m3u8 URL in double quotes
            r'(https?://[^\s<>"\']*\.m3u8[^\s<>"\']*)',  # Any m3u8 URL
        ]
        
        m3u8_url = None
        for pattern in m3u8_patterns:
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                m3u8_url = match.group(1)
                print(f"[INFO] Found M3U8 URL: {m3u8_url}")
                break
        
        if not m3u8_url:
            return {
                'success': False,
                'message': 'M3U8 URL not found in embed page',
                'file_path': None
            }
        
        # Step 3: Fetch the M3U8 content
        print(f"[INFO] Fetching M3U8 file: {m3u8_url}")
        m3u8_response = scraper.get(m3u8_url, headers={'Referer': embed_url}, timeout=30)
        
        if m3u8_response.status_code != 200:
            return {
                'success': False,
                'message': f'Failed to fetch M3U8 file. HTTP Status: {m3u8_response.status_code}',
                'file_path': None
            }
        
        print(f"[INFO] Successfully fetched M3U8 content ({len(m3u8_response.text)} bytes)")
        
        # Step 4: Process M3U8 content and complete relative URLs
        m3u8_content = m3u8_response.text
        lines = m3u8_content.split('\n')
        processed_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            # Check if line is not a comment and not empty
            if stripped_line and not stripped_line.startswith('#'):
                # If it's a relative URL, make it absolute
                if not stripped_line.startswith('http://') and not stripped_line.startswith('https://'):
                    # Complete the relative URL using urljoin
                    absolute_url = urljoin(m3u8_url, stripped_line)
                    processed_lines.append(absolute_url)
                    print(f"[INFO] Converted relative URL: {stripped_line} -> {absolute_url}")
                else:
                    processed_lines.append(stripped_line)
            else:
                processed_lines.append(stripped_line)
        
        # Reconstruct the M3U8 content
        processed_content = '\n'.join(processed_lines)
        
        # Step 5: Write to file
        output_file = os.path.join(folder_path, f'{stream_id}.m3u8')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        print(f"[SUCCESS] M3U8 file saved to: {output_file}")
        
        return {
            'success': True,
            'message': 'M3U8 file successfully downloaded and processed',
            'file_path': output_file,
            'm3u8_url': m3u8_url
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'file_path': None
        }


def process_all_streams(config_file='streams_config.json', delay=2):
    """
    Process all streams from the JSON config file
    
    Args:
        config_file (str): Path to the JSON config file
        delay (int): Delay in seconds between requests to avoid rate limiting
    
    Returns:
        dict: Summary of processed streams
    """
    # Load the config file
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            streams = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Config file '{config_file}' not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in config file: {e}")
        return None
    
    print(f"[INFO] Loaded {len(streams)} streams from config file")
    print("=" * 80)
    
    # Statistics
    successful = 0
    failed = 0
    failed_streams = []
    
    # Process each stream
    for idx, stream in enumerate(streams, 1):
        country = stream['country']
        subdivision = stream['subdivision']
        folder_name = stream['folder_name']
        stream_id = stream['stream_id']
        name = stream['name']
        referer = stream['referer']
        
        print(f"\n[{idx}/{len(streams)}] Processing: {name} ({country}/{subdivision}/{folder_name})")
        print("-" * 80)
        
        result = download_stream_manifest(
            stream_id=stream_id,
            referer=referer,
            country=country,
            subdivision=subdivision,
            folder_name=folder_name
        )
        
        if result['success']:
            successful += 1
            print(f"✓ SUCCESS: {name}")
        else:
            failed += 1
            failed_streams.append({
                'name': name,
                'location': f"{country}/{subdivision}/{folder_name}",
                'stream_id': stream_id,
                'error': result['message']
            })
            print(f"✗ FAILED: {name} - {result['message']}")
        
        # Delay between requests to avoid rate limiting
        if idx < len(streams):
            print(f"[INFO] Waiting {delay} seconds before next request...")
            time.sleep(delay)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total streams: {len(streams)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed_streams:
        print("\nFailed streams:")
        for stream in failed_streams:
            print(f"  - {stream['name']} ({stream['location']}/{stream['stream_id']})")
            print(f"    Error: {stream['error']}")
    
    return {
        'total': len(streams),
        'successful': successful,
        'failed': failed,
        'failed_streams': failed_streams
    }


if __name__ == '__main__':
    # Process all streams
    result = process_all_streams(config_file='galata_ai-config.json', delay=1)
    
    if result:
        print("\n" + "=" * 80)
        print("Processing complete!")
        print(f"Check the created folders for M3U8 files")
